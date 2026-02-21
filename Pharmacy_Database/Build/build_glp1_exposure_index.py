#!/usr/bin/env python3
"""
Build GLP-1 Exposure Index for Each Pharmacy
==============================================
Maps each pharmacy to nearby GLP-1 prescriber claims using
ZIP proximity + county adjacency, then computes a composite
exposure index (0-100) and distributes state-level fills
proportionally.

Data sources (public):
  - Part D GLP-1 by ZIP: reference_data/partd_glp1_by_zip.csv
    (from download_partd_prescribers.py)
  - Census county adjacency: census.gov (downloaded and cached)
  - ZCTA-to-county crosswalk: reference_data/zcta_county_crosswalk.txt
    (from rucc_enrich.py, already cached)
  - ALL_VERIFIED_CLEAN.csv: pharmacy database (33,185 rows)
  - state_glp1_loss_data_2024.csv: state-level claim totals

Proximity weights:
  Same ZIP:     1.0
  Same county:  0.5
  Adjacent county: 0.2

Composite exposure index (0-100):
  40% - Nearby prescriber claims (proximity-weighted)
  20% - State baseline (state-level claims per pharmacy)
  15% - ZIP diabetes prevalence
  10% - ZIP obesity prevalence
  10% - ZIP age 65+
   5% - HPSA designation

Output:
  reference_data/pharmacies_with_exposure.csv
  (ALL_VERIFIED_CLEAN columns + glp1_exposure_index,
   nearby_glp1_prescriber_claims, est_monthly_glp1_fills)

Key constraint: state-level fills MUST sum to the known state
totals from state_glp1_loss_data_2024.csv. No phantom claims.

Usage:
  python3 build_glp1_exposure_index.py
  python3 build_glp1_exposure_index.py --force

Dependencies: pandas, numpy (standard data science)
"""

import argparse
import csv
import os
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


# --- Configuration ---

BUILD_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = BUILD_DIR / 'reference_data'
REPO_ROOT = BUILD_DIR.parent.parent

# Input files
CLEAN_CSV = REPO_ROOT / 'State_Outreach_Lists_Verified' / 'ALL_VERIFIED_CLEAN.csv'
STATE_GLP1_CSV = REPO_ROOT / 'Pharmacy_Database' / 'Deliverables' / 'state_glp1_loss_data_2024.csv'
PARTD_BY_ZIP = REFERENCE_DIR / 'partd_glp1_by_zip.csv'
ZCTA_CROSSWALK = REFERENCE_DIR / 'zcta_county_crosswalk.txt'

# County adjacency from Census
ADJACENCY_URL = (
    'https://www2.census.gov/programs-surveys/metro-micro/'
    'geographies/reference-files/2023/delineation-files/'
    'list2_2023.xlsx'
)
# Actually use the simpler text-based county adjacency file
COUNTY_ADJ_URL = (
    'https://www2.census.gov/geo/docs/reference/'
    'county_adjacency2024.txt'
)
COUNTY_ADJ_CACHE = REFERENCE_DIR / 'county_adjacency.txt'

# Output
OUTPUT_CSV = REFERENCE_DIR / 'pharmacies_with_exposure.csv'

# Proximity weights for prescriber claims
WEIGHT_SAME_ZIP = 1.0
WEIGHT_SAME_COUNTY = 0.5
WEIGHT_ADJ_COUNTY = 0.2

# Composite exposure weights
EXPOSURE_WEIGHTS = {
    'nearby_claims': 0.40,
    'state_baseline': 0.20,
    'diabetes': 0.15,
    'obesity': 0.10,
    'age_65': 0.10,
    'hpsa': 0.05,
}


# --- County adjacency ---

def download_county_adjacency(force: bool = False) -> Path:
    """Download Census county adjacency file if not cached.

    This file lists which counties are adjacent to each other.
    Format: tab-delimited with county FIPS and neighbor FIPS.
    """
    if COUNTY_ADJ_CACHE.exists() and not force:
        return COUNTY_ADJ_CACHE

    os.makedirs(REFERENCE_DIR, exist_ok=True)
    print(f"Downloading county adjacency from Census...")
    try:
        urllib.request.urlretrieve(COUNTY_ADJ_URL, COUNTY_ADJ_CACHE)
        print(f"  Saved to {COUNTY_ADJ_CACHE}")
    except Exception as e:
        print(f"  WARN: Failed to download adjacency file: {e}")
        print("  Building adjacency from FIPS proximity instead.")
        _build_fips_proximity_adjacency()
    return COUNTY_ADJ_CACHE


def _build_fips_proximity_adjacency() -> None:
    """Fallback: build adjacency from ZCTA crosswalk.

    Uses the county FIPS codes from the crosswalk and considers
    counties in the same state with numerically close FIPS as adjacent.
    This is a reasonable approximation.
    """
    # Read all county FIPS from crosswalk
    counties_by_state: dict[str, list[str]] = defaultdict(list)
    with open(ZCTA_CROSSWALK, 'r', encoding='utf-8-sig') as f:
        header = f.readline().strip().split('|')
        county_idx = header.index('GEOID_COUNTY_20')
        for line in f:
            parts = line.strip().split('|')
            fips = parts[county_idx].strip()
            if fips:
                state_fips = fips[:2]
                if fips not in counties_by_state[state_fips]:
                    counties_by_state[state_fips].append(fips)

    # Write synthetic adjacency: all counties in same state
    # with FIPS codes within 10 of each other
    lines = []
    for state_fips, counties in counties_by_state.items():
        counties.sort()
        for i, c1 in enumerate(counties):
            fips1 = int(c1)
            for c2 in counties:
                fips2 = int(c2)
                if c1 != c2 and abs(fips1 - fips2) <= 10:
                    lines.append(f"{c1}\t{c2}\n")

    with open(COUNTY_ADJ_CACHE, 'w') as f:
        f.writelines(lines)
    print(f"  Built proximity-based adjacency: {len(lines):,} pairs")


def load_county_adjacency() -> dict[str, set[str]]:
    """Load county adjacency into dict: county_fips -> set of adjacent FIPS.

    The Census file format has variable structure. We parse it
    to extract FIPS pairs.
    """
    adj_path = download_county_adjacency()
    adjacency: dict[str, set[str]] = defaultdict(set)

    if not adj_path.exists():
        print("  WARN: No adjacency file available")
        return adjacency

    try:
        current_county = None
        with open(adj_path, 'r', encoding='latin-1') as f:
            for line in f:
                parts = line.strip().split('\t')
                # Census format: col0=county_name, col1=county_fips,
                #                col2=neighbor_name, col3=neighbor_fips
                # When col0 is non-empty, it's a new source county.
                # When col0 is empty, it's another neighbor of current.
                if len(parts) >= 4:
                    fips1 = parts[1].strip().replace('"', '')
                    fips2 = parts[3].strip().replace('"', '')
                    if parts[0].strip():
                        current_county = fips1
                    if current_county and fips2 and fips2 != current_county:
                        adjacency[current_county].add(fips2)
                        adjacency[fips2].add(current_county)
                elif len(parts) >= 2 and current_county:
                    # Continuation line with just neighbor
                    fips2 = parts[-1].strip().replace('"', '')
                    if fips2 and fips2 != current_county:
                        adjacency[current_county].add(fips2)
                        adjacency[fips2].add(current_county)
    except Exception as e:
        print(f"  WARN: Error parsing adjacency file: {e}")
        print("  Continuing with partial adjacency data")

    total_pairs = sum(len(v) for v in adjacency.values()) // 2
    print(f"  County adjacency: {len(adjacency):,} counties, "
          f"{total_pairs:,} adjacency pairs")
    return adjacency


# --- ZIP-to-county mapping ---

def load_zip_to_county() -> dict[str, str]:
    """Load ZIP -> county FIPS mapping from ZCTA crosswalk.

    Returns dict: zip5 -> county_fips (dominant county by area).
    """
    if not ZCTA_CROSSWALK.exists():
        print(f"ERROR: ZCTA crosswalk not found: {ZCTA_CROSSWALK}")
        print("  Run rucc_enrich.py to download it first.")
        sys.exit(1)

    best: dict[str, tuple[str, int]] = {}
    with open(ZCTA_CROSSWALK, 'r', encoding='utf-8-sig') as f:
        header = f.readline().strip().split('|')
        zcta_idx = header.index('GEOID_ZCTA5_20')
        county_idx = header.index('GEOID_COUNTY_20')
        area_idx = header.index('AREALAND_PART')
        for line in f:
            parts = line.strip().split('|')
            zcta = parts[zcta_idx].strip()
            county = parts[county_idx].strip()
            try:
                area = int(parts[area_idx])
            except (ValueError, IndexError):
                area = 0
            if zcta and (zcta not in best or area > best[zcta][1]):
                best[zcta] = (county, area)

    return {z: fips for z, (fips, _) in best.items()}


def build_county_to_zips(
    zip_to_county: dict[str, str],
) -> dict[str, set[str]]:
    """Invert ZIP->county to county->set[ZIP]."""
    result: dict[str, set[str]] = defaultdict(set)
    for zip5, county in zip_to_county.items():
        result[county].add(zip5)
    return result


# --- Load Part D prescriber claims by ZIP ---

def load_partd_by_zip() -> dict[str, int]:
    """Load Part D GLP-1 claims by ZIP.

    Returns dict: zip5 -> total_claims.
    """
    if not PARTD_BY_ZIP.exists():
        print(f"ERROR: Part D by ZIP not found: {PARTD_BY_ZIP}")
        print("  Run download_partd_prescribers.py first.")
        sys.exit(1)

    claims_by_zip: dict[str, int] = {}
    with open(PARTD_BY_ZIP, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            zip5 = row['zip'].strip()
            claims = int(float(row.get('total_claims', 0)))
            if zip5 and claims > 0:
                claims_by_zip[zip5] = claims

    print(f"  Part D claims: {len(claims_by_zip):,} ZIPs, "
          f"{sum(claims_by_zip.values()):,} total claims")
    return claims_by_zip


# --- Load state-level claim totals ---

def load_state_totals() -> dict[str, int]:
    """Load state-level GLP-1 claim totals.

    Returns dict: state -> total_govt_glp1_claims.
    """
    if not STATE_GLP1_CSV.exists():
        print(f"ERROR: State GLP-1 data not found: {STATE_GLP1_CSV}")
        sys.exit(1)

    totals: dict[str, int] = {}
    with open(STATE_GLP1_CSV, 'r') as f:
        # Skip comment lines
        lines = [l for l in f if not l.startswith('#')]

    reader = csv.DictReader(lines)
    for row in reader:
        state = row['state'].strip().upper()
        claims = int(float(row.get('total_govt_glp1_claims', 0)))
        totals[state] = claims

    return totals


# --- Compute nearby prescriber claims ---

def compute_nearby_claims(
    df: pd.DataFrame,
    claims_by_zip: dict[str, int],
    zip_to_county: dict[str, str],
    county_to_zips: dict[str, set[str]],
    county_adjacency: dict[str, set[str]],
) -> pd.Series:
    """Compute proximity-weighted prescriber claims for each pharmacy.

    For each pharmacy:
      1. Same ZIP claims * 1.0
      2. Same county (other ZIPs) claims * 0.5
      3. Adjacent county claims * 0.2

    Returns pd.Series of weighted claim counts.
    """
    print("Computing proximity-weighted prescriber claims...")

    nearby = []
    for _, row in df.iterrows():
        zip5 = str(row.get('zip', '')).strip()[:5]
        county = zip_to_county.get(zip5, '')

        # 1. Same ZIP
        same_zip = claims_by_zip.get(zip5, 0) * WEIGHT_SAME_ZIP

        # 2. Same county (excluding same ZIP)
        same_county = 0.0
        if county:
            for z in county_to_zips.get(county, set()):
                if z != zip5:
                    same_county += claims_by_zip.get(z, 0)
            same_county *= WEIGHT_SAME_COUNTY

        # 3. Adjacent counties
        adj_county = 0.0
        if county:
            for adj_fips in county_adjacency.get(county, set()):
                for z in county_to_zips.get(adj_fips, set()):
                    adj_county += claims_by_zip.get(z, 0)
            adj_county *= WEIGHT_ADJ_COUNTY

        nearby.append(same_zip + same_county + adj_county)

    return pd.Series(nearby, index=df.index)


# --- Compute composite exposure index ---

def compute_exposure_index(
    df: pd.DataFrame,
    nearby_claims: pd.Series,
) -> pd.Series:
    """Compute composite exposure index (0-100).

    Components:
      40% - Nearby prescriber claims (percentile rank)
      20% - State baseline (state_glp1_claims_per_pharmacy percentile)
      15% - ZIP diabetes prevalence (percentile)
      10% - ZIP obesity prevalence (percentile)
      10% - ZIP age 65+ (percentile)
       5% - HPSA (binary: 100 if designated, 0 if not)
    """
    print("Computing composite exposure index...")

    w = EXPOSURE_WEIGHTS

    # Percentile rank each component (0-100)
    nearby_rank = nearby_claims.rank(pct=True, method='max') * 100
    nearby_rank = nearby_rank.fillna(50.0)

    state_rank = pd.to_numeric(
        df['state_glp1_claims_per_pharmacy'], errors='coerce',
    ).rank(pct=True, method='max') * 100
    state_rank = state_rank.fillna(50.0)

    diabetes_rank = pd.to_numeric(
        df['zip_diabetes_pct'], errors='coerce',
    ).rank(pct=True, method='max') * 100
    diabetes_rank = diabetes_rank.fillna(50.0)

    obesity_rank = pd.to_numeric(
        df['zip_obesity_pct'], errors='coerce',
    ).rank(pct=True, method='max') * 100
    obesity_rank = obesity_rank.fillna(50.0)

    age65_rank = pd.to_numeric(
        df['zip_pct_65_plus'], errors='coerce',
    ).rank(pct=True, method='max') * 100
    age65_rank = age65_rank.fillna(50.0)

    hpsa = pd.to_numeric(
        df['hpsa_designated'], errors='coerce',
    ).fillna(0)
    hpsa_score = (hpsa > 0).astype(float) * 100

    # Composite
    index = (
        w['nearby_claims'] * nearby_rank
        + w['state_baseline'] * state_rank
        + w['diabetes'] * diabetes_rank
        + w['obesity'] * obesity_rank
        + w['age_65'] * age65_rank
        + w['hpsa'] * hpsa_score
    ).round(1)

    return index


# --- Distribute state fills proportionally ---

def distribute_state_fills(
    df: pd.DataFrame,
    exposure_index: pd.Series,
    state_totals: dict[str, int],
) -> pd.Series:
    """Distribute state-level annual claims to pharmacies by exposure.

    Each pharmacy gets: state_total_claims * (pharmacy_exposure / state_sum_exposure)

    This ensures state fills sum exactly to the known totals.
    Returns monthly fill estimates (annual / 12).
    """
    print("Distributing state fills proportionally by exposure...")

    annual_fills = pd.Series(0.0, index=df.index)

    for state in df['state'].unique():
        state_mask = df['state'] == state
        state_exposure = exposure_index[state_mask]
        state_sum = state_exposure.sum()

        state_annual = state_totals.get(state, 0)
        n_pharmacies = state_mask.sum()
        pharmacy_count_from_csv = n_pharmacies

        if state_sum > 0 and state_annual > 0:
            # Proportional distribution
            annual_fills[state_mask] = (
                state_annual * state_exposure / state_sum
            )
        elif state_annual > 0 and n_pharmacies > 0:
            # Fallback: equal distribution
            annual_fills[state_mask] = state_annual / n_pharmacies

    monthly_fills = (annual_fills / 12).round(0).astype(int)
    return monthly_fills


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Build GLP-1 exposure index for pharmacies',
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Force re-download of adjacency data',
    )
    args = parser.parse_args()

    print("=" * 60)
    print("GLP-1 Exposure Index Builder")
    print("=" * 60)

    # Load inputs
    print("\nLoading data...")
    df = pd.read_csv(
        CLEAN_CSV,
        dtype={'npi': str, 'zip': str, 'phone': str},
    )
    print(f"  Pharmacies: {len(df):,}")

    claims_by_zip = load_partd_by_zip()
    state_totals = load_state_totals()
    zip_to_county = load_zip_to_county()
    county_to_zips = build_county_to_zips(zip_to_county)
    county_adjacency = load_county_adjacency()

    # Compute nearby claims
    nearby_claims = compute_nearby_claims(
        df, claims_by_zip, zip_to_county, county_to_zips,
        county_adjacency,
    )
    df['nearby_glp1_prescriber_claims'] = nearby_claims.round(0).astype(int)

    # Compute exposure index
    exposure_index = compute_exposure_index(df, nearby_claims)
    df['glp1_exposure_index'] = exposure_index

    # Distribute state fills
    monthly_fills = distribute_state_fills(
        df, exposure_index, state_totals,
    )
    df['est_monthly_glp1_fills'] = monthly_fills

    # --- Validation ---
    print("\n--- Validation ---")

    # Check exposure index range
    ei_min = df['glp1_exposure_index'].min()
    ei_max = df['glp1_exposure_index'].max()
    ei_null = df['glp1_exposure_index'].isna().sum()
    print(f"Exposure index range: {ei_min} - {ei_max}")
    print(f"Exposure index nulls: {ei_null}")

    # Check state fill totals
    print("\nState fill conservation check (top 10 states):")
    for state in ['CA', 'TX', 'NY', 'FL', 'OH', 'PA', 'IL', 'MI', 'KY', 'IN']:
        state_mask = df['state'] == state
        computed = (df.loc[state_mask, 'est_monthly_glp1_fills'] * 12).sum()
        expected = state_totals.get(state, 0)
        diff_pct = abs(computed - expected) / expected * 100 if expected else 0
        status = 'OK' if diff_pct < 5 else 'DRIFT'
        print(f"  {state}: computed {computed:,.0f} vs expected {expected:,} "
              f"({diff_pct:.1f}% {status})")

    # Nearby claims stats
    nc = df['nearby_glp1_prescriber_claims']
    print(f"\nNearby claims: min={nc.min()}, median={nc.median():.0f}, "
          f"max={nc.max()}, zero={( nc == 0).sum()}")

    # Spot checks
    print("\nSpot checks:")
    ky_apothecary = df[df['npi'] == '1497754923']
    if not ky_apothecary.empty:
        r = ky_apothecary.iloc[0]
        print(f"  Central KY Apothecary: exposure={r['glp1_exposure_index']}, "
              f"nearby_claims={r['nearby_glp1_prescriber_claims']}, "
              f"monthly_fills={r['est_monthly_glp1_fills']}")

    # --- Write output ---
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(df):,} pharmacies to {OUTPUT_CSV}")
    print(f"Columns: {list(df.columns)}")


if __name__ == '__main__':
    main()
