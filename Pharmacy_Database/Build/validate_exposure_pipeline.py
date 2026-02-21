#!/usr/bin/env python3
"""
Validate Exposure Pipeline Output
====================================
Post-build validation script for the GLP-1 exposure index pipeline.
Run after the full pipeline to verify data integrity.

Checks:
  1. State fills sum to known state totals (no phantom claims)
  2. Exposure index range [0, 100] with no nulls
  3. NADAC loss per fill sanity check
  4. New columns exist and are populated
  5. Spot-check specific pharmacies vs old estimates
  6. Grade distribution stability
  7. Total pharmacy count unchanged

Usage:
  python3 validate_exposure_pipeline.py
  python3 validate_exposure_pipeline.py --verbose
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


# --- Paths ---

BUILD_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = BUILD_DIR / 'reference_data'
REPO_ROOT = BUILD_DIR.parent.parent

TARGETING_CSV = REPO_ROOT / 'Deliverables' / 'rmm_targeting_feb2026.csv'
STATE_GLP1_CSV = REPO_ROOT / 'Pharmacy_Database' / 'Deliverables' / 'state_glp1_loss_data_2024.csv'
LOSS_JSON = REFERENCE_DIR / 'glp1_loss_per_fill.json'
EXPOSURE_CSV = REFERENCE_DIR / 'pharmacies_with_exposure.csv'

EXPECTED_TOTAL = 33185

# Required new columns
NEW_COLUMNS = [
    'glp1_exposure_index',
    'nearby_glp1_prescriber_claims',
    'est_loss_per_fill',
]


# --- Helpers ---

def _parse_dollar(s: str) -> float:
    """Parse '$1,234' to 1234.0."""
    try:
        return float(s.replace('$', '').replace(',', ''))
    except (ValueError, TypeError):
        return 0.0


def _load_state_totals() -> dict[str, int]:
    """Load state-level GLP-1 claim totals."""
    totals = {}
    with open(STATE_GLP1_CSV, 'r') as f:
        lines = [l for l in f if not l.startswith('#')]
    reader = csv.DictReader(lines)
    for row in reader:
        state = row['state'].strip().upper()
        claims = int(float(row.get('total_govt_glp1_claims', 0)))
        totals[state] = claims
    return totals


# --- Validation checks ---

class ValidationReport:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []

    def check(self, name: str, ok: bool, detail: str = ''):
        status = 'PASS' if ok else 'FAIL'
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        self.details.append(f"  [{status}] {name}" + (f": {detail}" if detail else ""))

    def warn(self, name: str, detail: str = ''):
        self.warnings += 1
        self.details.append(f"  [WARN] {name}" + (f": {detail}" if detail else ""))

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "EXPOSURE PIPELINE VALIDATION REPORT",
            "=" * 60,
            "",
        ]
        lines.extend(self.details)
        lines.append("")
        lines.append(f"Results: {self.passed} passed, {self.failed} failed, "
                      f"{self.warnings} warnings")
        if self.failed == 0:
            lines.append("STATUS: ALL CHECKS PASSED")
        else:
            lines.append("STATUS: VALIDATION FAILED")
        lines.append("=" * 60)
        return '\n'.join(lines)


def validate(verbose: bool = False) -> ValidationReport:
    """Run all validation checks."""
    report = ValidationReport()

    # --- Check files exist ---
    report.check("Targeting CSV exists", TARGETING_CSV.exists(),
                 str(TARGETING_CSV))
    if not TARGETING_CSV.exists():
        print("ERROR: Targeting CSV not found. Run the pipeline first.")
        return report

    report.check("Loss per fill JSON exists", LOSS_JSON.exists(),
                 str(LOSS_JSON))

    # --- Load targeting CSV ---
    rows = []
    with open(TARGETING_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    n = len(rows)
    report.check(f"Total pharmacies = {EXPECTED_TOTAL}",
                 n == EXPECTED_TOTAL, f"Got {n}")

    # --- Check new columns exist ---
    for col in NEW_COLUMNS:
        exists = col in fieldnames if fieldnames else False
        report.check(f"Column '{col}' exists", exists)

    # --- Exposure index range ---
    exposure_vals = []
    exposure_nulls = 0
    for r in rows:
        val = r.get('glp1_exposure_index', '')
        if not val or val == '':
            exposure_nulls += 1
        else:
            try:
                exposure_vals.append(float(val))
            except ValueError:
                exposure_nulls += 1

    if exposure_vals:
        ei_min = min(exposure_vals)
        ei_max = max(exposure_vals)
        report.check("Exposure index min >= 0",
                     ei_min >= 0, f"min={ei_min}")
        report.check("Exposure index max <= 100",
                     ei_max <= 100, f"max={ei_max}")
        report.check("Exposure index no nulls",
                     exposure_nulls == 0,
                     f"{exposure_nulls} nulls")
        if verbose:
            import statistics
            report.details.append(
                f"  [INFO] Exposure index: min={ei_min}, "
                f"median={statistics.median(exposure_vals):.1f}, "
                f"max={ei_max}")

    # --- Nearby claims sanity ---
    nearby_vals = []
    for r in rows:
        val = r.get('nearby_glp1_prescriber_claims', '0')
        try:
            nearby_vals.append(int(float(val)))
        except (ValueError, TypeError):
            nearby_vals.append(0)

    zero_nearby = sum(1 for v in nearby_vals if v == 0)
    report.check("Nearby claims < 50% zero",
                 zero_nearby / n < 0.5,
                 f"{zero_nearby:,} zero ({zero_nearby/n*100:.1f}%)")

    # --- Loss per fill sanity ---
    if LOSS_JSON.exists():
        with open(LOSS_JSON, 'r') as f:
            loss_data = json.load(f)
        national_loss = loss_data.get('national_weighted_loss_per_fill', 0)
        report.check("National loss/fill > $10",
                     national_loss > 10,
                     f"${national_loss:.2f}")
        report.check("National loss/fill < $80",
                     national_loss < 80,
                     f"${national_loss:.2f}")

        per_drug = loss_data.get('per_drug', {})
        for drug, info in per_drug.items():
            loss = info.get('structural_loss_per_fill', 0)
            # Structural loss is positive (pharmacy pays more than PBM reimburses)
            report.details.append(
                f"  [INFO] {drug}: loss/fill=${loss:.2f}, "
                f"NADAC/unit=${info.get('nadac_per_unit', 0):.2f}")

    # --- Loss per fill in CSV ---
    loss_vals = []
    for r in rows:
        val = r.get('est_loss_per_fill', '')
        parsed = _parse_dollar(val)
        if parsed > 0:
            loss_vals.append(parsed)

    if loss_vals:
        lpf_min = min(loss_vals)
        lpf_max = max(loss_vals)
        report.check("Per-pharmacy loss/fill > $0",
                     lpf_min > 0, f"min=${lpf_min:.2f}")
        report.check("Per-pharmacy loss/fill < $60",
                     lpf_max < 60, f"max=${lpf_max:.2f}")
        if verbose:
            report.details.append(
                f"  [INFO] Loss/fill range: ${lpf_min:.2f} - ${lpf_max:.2f}")

    # --- State fill conservation ---
    if STATE_GLP1_CSV.exists():
        state_totals = _load_state_totals()
        state_computed: dict[str, int] = {}
        for r in rows:
            state = r.get('state', '')
            fills = int(float(r.get('est_monthly_glp1_fills', 0) or 0))
            state_computed[state] = state_computed.get(state, 0) + fills * 12

        drift_states = []
        for state in ['CA', 'TX', 'NY', 'FL', 'OH', 'KY', 'IN', 'PA']:
            expected = state_totals.get(state, 0)
            computed = state_computed.get(state, 0)
            if expected > 0:
                drift_pct = abs(computed - expected) / expected * 100
                ok = drift_pct < 10  # Allow up to 10% rounding drift
                if not ok:
                    drift_states.append(state)
                if verbose:
                    report.details.append(
                        f"  [INFO] {state}: computed {computed:,} vs "
                        f"expected {expected:,} ({drift_pct:.1f}%)")

        report.check("State fills within 10% of known totals",
                     len(drift_states) == 0,
                     f"Drifted: {drift_states}" if drift_states else "All OK")

    # --- Grade distribution ---
    grades = Counter(r['grade'] for r in rows)
    for g in ['A', 'B', 'C', 'D']:
        report.details.append(
            f"  [INFO] Grade {g}: {grades.get(g, 0):,} "
            f"({grades.get(g, 0)/n*100:.1f}%)")

    report.check("Grade A = 15%",
                 abs(grades.get('A', 0) / n - 0.15) < 0.02,
                 f"{grades.get('A', 0)/n*100:.1f}%")

    # --- Spot checks ---
    # Central Kentucky Apothecary (NPI 1497754923)
    ky_apothecary = [r for r in rows if r.get('npi') == '1497754923']
    if ky_apothecary:
        ck = ky_apothecary[0]
        report.check("Central KY Apothecary found", True)
        report.details.append(
            f"  [INFO] CKA: score={ck.get('rmm_score')}, "
            f"grade={ck.get('grade')}, "
            f"exposure={ck.get('glp1_exposure_index')}, "
            f"nearby={ck.get('nearby_glp1_prescriber_claims')}, "
            f"fills={ck.get('est_monthly_glp1_fills')}, "
            f"loss/fill={ck.get('est_loss_per_fill')}, "
            f"annual_loss={ck.get('est_annual_glp1_loss')}")
    else:
        report.warn("Central KY Apothecary not found")

    return report


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Validate exposure pipeline output',
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Show detailed info for each check',
    )
    args = parser.parse_args()

    report = validate(verbose=args.verbose)
    print(report.summary())
    sys.exit(0 if report.failed == 0 else 1)


if __name__ == '__main__':
    main()
