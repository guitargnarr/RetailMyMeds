#!/usr/bin/env python3
"""
RMM Pharmacy Scoring Engine
============================
7-factor weighted percentile-rank scoring system.

Input:  State_Outreach_Lists_Verified/ALL_VERIFIED_CLEAN.csv (33,185 rows)
Output: Deliverables/rmm_targeting_feb2026.csv (full scored)
        Deliverables/rmm_targeting_grade_A_feb2026.csv (Grade A subset)

Scoring factors (weights sum to 1.0):
  25% - State GLP-1 cost per pharmacy (higher = more GLP-1 exposure)
  20% - ZIP diabetes prevalence (higher = more need)
  15% - ZIP % age 65+ (higher = more Medicare exposure)
  10% - ZIP obesity prevalence (higher = comorbidity signal)
  10% - HPSA designation (binary: 100 if designated, 0 if not)
  10% - ZIP median income (INVERTED: lower income = higher score)
  10% - ZIP population (INVERTED: smaller market = less competition)

Percentile rank method: pandas .rank(pct=True, method='max') * 100
  - method='max' assigns tied values the highest rank in the tie group
  - Null handling: sentinel income values (<-999999) become NaN -> fillna(50.0)
  - Zero income is kept as a real value (lowest income = highest inverted rank)

Grade assignment by cumulative cutoff using round():
  A = top round(n * 0.15) pharmacies  (Immediate outreach)
  B = next round(n * 0.40) - A        (High priority)
  C = next round(n * 0.70) - A - B    (Standard)
  D = remainder                        (Monitor)

Usage:
  python3 score_pharmacies.py
  python3 score_pharmacies.py --input clean.csv --output-dir out/

Dependencies: pandas, numpy (standard data science stack)
"""

import csv
import os
import sys
import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from rucc_enrich import build_zip_lookup

# --- Configuration ---

WEIGHTS = {
    'state_glp1_cost_per_pharmacy': 0.25,
    'zip_diabetes_pct': 0.20,
    'zip_pct_65_plus': 0.15,
    'zip_obesity_pct': 0.10,
    'hpsa_score': 0.10,
    'zip_median_income': 0.10,  # inverted
    'zip_population': 0.10,     # inverted
}

FACTORS_NORMAL = ['state_glp1_cost_per_pharmacy', 'zip_diabetes_pct',
                  'zip_obesity_pct', 'zip_pct_65_plus']
FACTORS_INVERTED = ['zip_median_income', 'zip_population']

# Grade thresholds (cumulative fractions, applied via round(n * threshold))
GRADE_THRESHOLDS = [
    ('A', 0.15),
    ('B', 0.40),
    ('C', 0.70),
    ('D', 1.00),
]

GRADE_PRIORITY = {
    'A': 'Immediate',
    'B': 'High',
    'C': 'Standard',
    'D': 'Monitor',
}

# GLP-1 loss: $37 per fill (NCPA survey data)
LOSS_PER_FILL = 37

OUTPUT_COLUMNS = [
    'npi', 'pharmacy_name', 'owner_name', 'city', 'state', 'zip', 'phone',
    'grade', 'outreach_priority', 'rmm_score',
    'est_monthly_glp1_fills', 'est_annual_glp1_loss',
    'hpsa_designated', 'hpsa_score',
    'zip_diabetes_pct', 'zip_obesity_pct', 'zip_pct_65_plus',
    'zip_median_income', 'zip_population', 'state_glp1_cost_per_pharmacy',
    'county_fips', 'county_name', 'rucc_code', 'rural_classification',
]


# --- Helpers ---

def format_phone(raw: object) -> str:
    """Format 10-digit phone as (XXX) XXX-XXXX."""
    digits = ''.join(c for c in str(raw) if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return raw


def format_currency(val: object) -> str:
    """Format number as $X,XXX. Returns 'N/A' for NaN/None."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 'N/A'
    return f"${int(round(val)):,}"


# --- Main ---

ScoredRow = dict[str, object]


def score_pharmacies(input_path: str, output_dir: str) -> list[ScoredRow]:
    """Score pharmacies from clean CSV and write targeting CSVs."""

    df = pd.read_csv(
        input_path, dtype={'npi': str, 'zip': str, 'phone': str},
    )
    n = len(df)
    print(f"Scoring {n:,} pharmacies from {input_path}")

    # Convert numeric columns
    numeric_cols = [
        'state_glp1_cost_per_pharmacy',
        'zip_diabetes_pct', 'zip_obesity_pct',
        'zip_pct_65_plus', 'zip_median_income',
        'zip_population', 'hpsa_score',
        'hpsa_designated',
        'state_glp1_claims_per_pharmacy',
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Null handling: sentinel income -> NaN (zero stays)
    sentinel = df['zip_median_income'] < -999999
    df.loc[sentinel, 'zip_median_income'] = np.nan

    # --- Compute percentile ranks ---

    # Normal factors: higher raw value = higher rank
    for col in FACTORS_NORMAL:
        df[f'{col}_rank'] = df[col].rank(pct=True, method='max') * 100
        df[f'{col}_rank'] = df[f'{col}_rank'].fillna(50.0)

    # Inverted factors: lower raw value = higher rank
    for col in FACTORS_INVERTED:
        df[f'{col}_rank'] = (1 - df[col].rank(pct=True, method='max')) * 100
        df[f'{col}_rank'] = df[f'{col}_rank'].fillna(50.0)

    # HPSA: binary 100/0
    df['hpsa_score_rank'] = (df['hpsa_designated'] > 0).astype(float) * 100

    # --- Composite score ---
    w = WEIGHTS
    r = {k: df[f'{k}_rank'] for k in w}
    df['rmm_score'] = (
        w['state_glp1_cost_per_pharmacy'] * r['state_glp1_cost_per_pharmacy']
        + w['zip_diabetes_pct'] * r['zip_diabetes_pct']
        + w['zip_pct_65_plus'] * r['zip_pct_65_plus']
        + w['zip_obesity_pct'] * r['zip_obesity_pct']
        + w['hpsa_score'] * r['hpsa_score']
        + w['zip_median_income'] * r['zip_median_income']
        + w['zip_population'] * r['zip_population']
    ).round(1)

    # --- GLP-1 fill estimates ---
    claims = df['state_glp1_claims_per_pharmacy']
    df['est_monthly_glp1_fills'] = (
        (claims / 12).round(0).fillna(0).astype(int)
    )
    df['est_annual_glp1_loss'] = (
        (claims * LOSS_PER_FILL).round(0).fillna(0).astype(int)
    )

    # --- Sort by score descending ---
    df = df.sort_values(
        'rmm_score', ascending=False,
    ).reset_index(drop=True)

    # --- Assign grades using round() cumulative cutoffs ---
    cumulative_cuts = {}
    for grade, threshold in GRADE_THRESHOLDS:
        cumulative_cuts[grade] = round(n * threshold)

    def assign_grade(idx):
        for grade, threshold in GRADE_THRESHOLDS:
            if (idx + 1) <= cumulative_cuts[grade]:
                return grade
        return 'D'

    df['grade'] = [assign_grade(i) for i in range(n)]
    df['outreach_priority'] = df['grade'].map(GRADE_PRIORITY)

    # --- Build RUCC lookup ---
    rucc_lookup = build_zip_lookup()

    # --- Format output columns ---
    output_rows = []
    for _, row in df.iterrows():
        income_val = row['zip_median_income']
        zip5 = str(row.get('zip', '')).strip()[:5]
        rucc_info = rucc_lookup.get(zip5, {})
        output_rows.append({
            'npi': row['npi'],
            'pharmacy_name': row.get(
                'display_name', row.get('pharmacy_name', ''),
            ),
            'owner_name': row.get('owner_name', ''),
            'city': row.get('city', ''),
            'state': row.get('state', ''),
            'zip': row.get('zip', ''),
            'phone': format_phone(row.get('phone', '')),
            'grade': row['grade'],
            'outreach_priority': row['outreach_priority'],
            'rmm_score': row['rmm_score'],
            'est_monthly_glp1_fills': row['est_monthly_glp1_fills'],
            'est_annual_glp1_loss': (
                format_currency(row['est_annual_glp1_loss'])
                if row['est_annual_glp1_loss'] else '$0'
            ),
            'hpsa_designated': (
                'Yes' if int(row.get('hpsa_designated', 0) or 0)
                else 'No'
            ),
            'hpsa_score': int(row.get('hpsa_score', 0) or 0),
            'zip_diabetes_pct': row.get('zip_diabetes_pct', ''),
            'zip_obesity_pct': row.get('zip_obesity_pct', ''),
            'zip_pct_65_plus': row.get('zip_pct_65_plus', ''),
            'zip_median_income': format_currency(income_val),
            'zip_population': row.get('zip_population', ''),
            'state_glp1_cost_per_pharmacy': format_currency(
                row.get('state_glp1_cost_per_pharmacy'),
            ),
            'county_fips': rucc_info.get('county_fips', ''),
            'county_name': rucc_info.get('county_name', ''),
            'rucc_code': rucc_info.get('rucc_code', ''),
            'rural_classification': rucc_info.get('rural_classification', ''),
        })

    # --- Write CSVs ---
    output_full = os.path.join(output_dir, 'rmm_targeting_feb2026.csv')
    with open(output_full, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    grade_a = [r for r in output_rows if r['grade'] == 'A']
    output_a = os.path.join(output_dir, 'rmm_targeting_grade_A_feb2026.csv')
    with open(output_a, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(grade_a)

    # --- Summary ---
    grades = Counter(r['grade'] for r in output_rows)
    print("\nGrade distribution:")
    for g in ['A', 'B', 'C', 'D']:
        pct = grades[g] / n * 100
        print(f"  Grade {g}: {grades[g]:,} ({pct:.1f}%)")

    scores = [r['rmm_score'] for r in output_rows]
    print(f"\nScore range: {min(scores)} - {max(scores)}")

    print("\nGrade A top 15 states:")
    state_counts = Counter(r['state'] for r in grade_a)
    for st, cnt in state_counts.most_common(15):
        print(f"  {st}: {cnt}")

    print(f"\nWrote {len(output_rows):,} to {output_full}")
    print(f"Wrote {len(grade_a):,} Grade A to {output_a}")

    # RUCC summary
    rucc_filled = sum(1 for r in output_rows if r['rucc_code'] != '')
    rucc_pct = rucc_filled / n * 100
    print(f"\nRUCC coverage: {rucc_filled:,}/{n:,} "
          f"({rucc_pct:.1f}%)")
    rural_counts = Counter(r['rural_classification'] for r in output_rows
                           if r['rural_classification'])
    for cls in ['Metro', 'Rural-Adjacent', 'Rural-Remote']:
        cnt = rural_counts.get(cls, 0)
        print(f"  {cls}: {cnt:,}")

    # Kentucky check
    ky = [r for r in output_rows if r['state'] == 'KY']
    ky_a = [r for r in ky if r['grade'] == 'A']
    print(f"\nKentucky: {len(ky)} total, {len(ky_a)} Grade A")
    if ky_a:
        top = ky_a[0]
        print(f"  Top KY: {top['pharmacy_name']}, "
              f"{top['city']} (score: {top['rmm_score']})")

    # Arica's pharmacy check
    arica = [r for r in output_rows if r['npi'] == '1497754923']
    if arica:
        a = arica[0]
        print(f"\nCentral Kentucky Apothecary: "
              f"score {a['rmm_score']}, grade {a['grade']}")

    # Big Jim's check
    bigjim = [r for r in output_rows
              if 'BIG JIM' in r['pharmacy_name'].upper()]
    for b in bigjim:
        print(f"Big Jim's: {b['pharmacy_name']}, {b['city']}, {b['state']}"
              f" (score: {b['rmm_score']}, grade: {b['grade']})")

    return output_rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RMM Pharmacy Scoring Engine')
    parser.add_argument(
        '--input', default=None,
        help='Path to clean verified CSV',
    )
    parser.add_argument(
        '--output-dir', default=None,
        help='Output directory for targeting CSVs',
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    input_path = (
        args.input
        or repo_root / 'State_Outreach_Lists_Verified'
        / 'ALL_VERIFIED_CLEAN.csv'
    )
    output_dir = args.output_dir or repo_root / 'Deliverables'

    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    score_pharmacies(str(input_path), str(output_dir))
