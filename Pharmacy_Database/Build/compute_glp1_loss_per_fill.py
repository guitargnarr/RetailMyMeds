#!/usr/bin/env python3
"""
Compute GLP-1 Loss Per Fill from NADAC Data
=============================================
Downloads NADAC (National Average Drug Acquisition Cost) from
data.medicaid.gov and computes per-drug structural loss for GLP-1s.

Structural loss = pharmacy acquisition cost (NADAC) - typical
reimbursement (WAC - 4%, which is a common PBM baseline).

Weights per-drug loss by Part D prescribing volume to produce
national and per-state weighted averages.

Data sources (public, no login):
  - NADAC: data.medicaid.gov (weekly pharmacy acquisition costs)
  - Part D drug mix: reference_data/partd_glp1_drug_mix.csv
    (from download_partd_prescribers.py)

Output:
  reference_data/glp1_loss_per_fill.json
  {
    "national_weighted_loss_per_fill": 23.45,
    "methodology": "...",
    "per_drug": {
      "semaglutide": {"nadac_per_unit": ..., "est_reimbursement": ...,
                       "structural_loss": ..., "national_claims_pct": ...},
      ...
    },
    "per_state": {
      "KY": {"weighted_loss_per_fill": 22.80, "dominant_drug": "semaglutide"},
      ...
    }
  }

Usage:
  python3 compute_glp1_loss_per_fill.py
  python3 compute_glp1_loss_per_fill.py --force

Dependencies: requests
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests")
    sys.exit(1)


# --- Configuration ---

REFERENCE_DIR = Path(__file__).resolve().parent / 'reference_data'

# NADAC REST API -- current NADAC rates
# Dataset: NADAC (National Average Drug Acquisition Cost)
# New endpoint format (old Socrata a4y5-998d is 404)
NADAC_API = 'https://data.medicaid.gov/api/1/datastore/query/f38d0706-1239-442c-a3cc-40ef1b686ac0/0'

# GLP-1 NDC search patterns (brand names to query NADAC)
GLP1_BRANDS = {
    'semaglutide': [
        'OZEMPIC', 'WEGOVY', 'RYBELSUS',
    ],
    'tirzepatide': [
        'MOUNJARO', 'ZEPBOUND',
    ],
    'liraglutide': [
        'VICTOZA', 'SAXENDA',
    ],
    'dulaglutide': [
        'TRULICITY',
    ],
    'exenatide': [
        'BYETTA', 'BYDUREON',
    ],
}

# Typical monthly supply units (for computing per-fill cost)
# Injectable pens are typically 1 box/month = ~3mL for semaglutide
# These are approximate unit counts per typical 30-day fill
UNITS_PER_FILL = {
    'semaglutide': 3.0,    # 3mL per pen box (Ozempic)
    'tirzepatide': 2.4,    # 2.4mL per pen box (Mounjaro)
    'liraglutide': 18.0,   # 18mL per pen box (Victoza)
    'dulaglutide': 2.0,    # 2mL (4 pens x 0.5mL)
    'exenatide': 2.4,      # 2.4mL
}

# GLP-1 underwater reimbursement model
# Pharmacies report consistent underwater reimbursement on GLP-1s.
# PBMs reimburse below acquisition cost on many GLP-1 NDCs.
# Industry sources (NCPA, Arica Collins) report 1-5% gross margin
# at best, with many fills underwater.
#
# We model: reimbursement = NADAC * REIMBURSEMENT_RATIO
# where REIMBURSEMENT_RATIO < 1.0 means underwater.
# Based on NCPA 2023 ($42/fill avg loss on ~$1000 acquisition):
#   loss_pct = 42/1000 = 4.2% underwater
# Conservative estimate: 3-5% below acquisition
REIMBURSEMENT_RATIO = 0.965  # PBM reimburses ~96.5% of NADAC (3.5% underwater)

# Part D drug mix input
DRUG_MIX_PATH = REFERENCE_DIR / 'partd_glp1_drug_mix.csv'

# Output
OUTPUT_PATH = REFERENCE_DIR / 'glp1_loss_per_fill.json'
NADAC_CACHE = REFERENCE_DIR / 'nadac_glp1_cache.json'


# --- Download NADAC ---

def download_nadac_glp1(force: bool = False) -> dict[str, dict]:
    """Download current NADAC prices for GLP-1 drugs.

    Returns dict: drug_generic -> {
        'nadac_per_unit': float,
        'brand_name': str,
        'effective_date': str,
    }
    Uses the most recent NADAC rate for each drug.
    """
    if NADAC_CACHE.exists() and not force:
        print(f"Loading cached NADAC data from {NADAC_CACHE}")
        with open(NADAC_CACHE, 'r') as f:
            return json.load(f)

    os.makedirs(REFERENCE_DIR, exist_ok=True)
    print("Downloading NADAC data for GLP-1 drugs...")

    drug_prices: dict[str, dict] = {}

    for generic, brands in GLP1_BRANDS.items():
        best_price = None
        best_date = ''
        best_brand = ''

        for brand in brands:
            # Query NADAC via new REST API
            params = {
                'limit': 10,
                'conditions[0][property]': 'ndc_description',
                'conditions[0][value]': brand,
                'conditions[0][operator]': 'contains',
                'sort[0][property]': 'effective_date',
                'sort[0][order]': 'desc',
            }

            retries = 0
            while retries < 3:
                try:
                    resp = requests.get(
                        NADAC_API, params=params, timeout=60,
                    )
                    resp.raise_for_status()
                    break
                except (requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError,
                        requests.exceptions.HTTPError) as e:
                    retries += 1
                    print(f"    Retry {retries}/3 for {brand}: {e}")
                    time.sleep(5 * retries)
            else:
                print(f"    WARN: Failed to fetch NADAC for {brand}")
                continue

            data = resp.json().get('results', [])
            if not data:
                print(f"    No NADAC data for {brand}")
                continue

            # Take the most recent price
            for row in data:
                try:
                    price = float(row.get('nadac_per_unit', 0))
                    date = row.get('effective_date', '')
                except (ValueError, TypeError):
                    continue

                if price > 0 and (best_price is None or date > best_date):
                    best_price = price
                    best_date = date
                    best_brand = row.get('ndc_description', brand)

            time.sleep(0.3)  # Rate limit

        if best_price:
            drug_prices[generic] = {
                'nadac_per_unit': round(best_price, 4),
                'brand_name': best_brand,
                'effective_date': best_date[:10],
            }
            print(f"  {generic}: ${best_price:.4f}/unit "
                  f"({best_brand}, {best_date[:10]})")
        else:
            print(f"  WARN: No NADAC price found for {generic}")

    # Cache
    with open(NADAC_CACHE, 'w') as f:
        json.dump(drug_prices, f, indent=2)
    print(f"  Cached to {NADAC_CACHE}")

    return drug_prices


# --- Compute structural loss ---

def compute_loss_per_drug(
    nadac_prices: dict[str, dict],
) -> dict[str, dict]:
    """Compute structural loss per fill for each GLP-1 drug.

    Structural loss = acquisition cost - PBM reimbursement
    Acquisition = NADAC * units_per_fill
    Reimbursement = NADAC * REIMBURSEMENT_RATIO * units_per_fill
    Loss = acquisition - reimbursement (positive = pharmacy loses money)

    Returns drug -> {nadac_per_unit, acquisition_per_fill,
                     est_reimbursement_per_fill, structural_loss_per_fill}
    """
    results = {}

    for drug, info in nadac_prices.items():
        nadac = info['nadac_per_unit']
        units = UNITS_PER_FILL.get(drug, 3.0)

        acquisition = nadac * units
        reimbursement = nadac * REIMBURSEMENT_RATIO * units
        loss = acquisition - reimbursement  # positive = underwater

        results[drug] = {
            'nadac_per_unit': round(nadac, 4),
            'units_per_fill': units,
            'acquisition_per_fill': round(acquisition, 2),
            'reimbursement_ratio': REIMBURSEMENT_RATIO,
            'est_reimbursement_per_fill': round(reimbursement, 2),
            'structural_loss_per_fill': round(loss, 2),
            'brand_name': info.get('brand_name', ''),
            'effective_date': info.get('effective_date', ''),
        }

    return results


# --- Weight by prescribing volume ---

def load_drug_mix() -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """Load Part D drug mix from CSV.

    Returns:
      national_weights: drug -> fraction of national claims
      state_weights: state -> drug -> fraction of state claims
    """
    if not DRUG_MIX_PATH.exists():
        print(f"WARN: Drug mix file not found: {DRUG_MIX_PATH}")
        print("  Run download_partd_prescribers.py first.")
        print("  Using equal weights as fallback.")
        equal = 1.0 / len(GLP1_BRANDS)
        return (
            {d: equal for d in GLP1_BRANDS},
            {},
        )

    national_claims: dict[str, int] = defaultdict(int)
    state_claims: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int),
    )

    with open(DRUG_MIX_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            drug = row['drug_generic'].strip().lower()
            state = row['state'].strip().upper()
            claims = int(float(row.get('total_claims', 0)))
            national_claims[drug] += claims
            state_claims[state][drug] += claims

    total_national = sum(national_claims.values())
    national_weights = {}
    for drug, cnt in national_claims.items():
        national_weights[drug] = cnt / total_national if total_national else 0

    state_weights = {}
    for state, drugs in state_claims.items():
        total_state = sum(drugs.values())
        state_weights[state] = {}
        for drug, cnt in drugs.items():
            state_weights[state][drug] = (
                cnt / total_state if total_state else 0
            )

    return national_weights, state_weights


def compute_weighted_loss(
    per_drug_loss: dict[str, dict],
    national_weights: dict[str, float],
    state_weights: dict[str, dict[str, float]],
) -> dict:
    """Compute weighted loss per fill nationally and per state.

    Returns full output dict for JSON serialization.
    """
    # National weighted average
    national_loss = 0.0
    for drug, info in per_drug_loss.items():
        weight = national_weights.get(drug, 0)
        national_loss += info['structural_loss_per_fill'] * weight

    # Per-drug with national weight
    per_drug_output = {}
    for drug, info in per_drug_loss.items():
        per_drug_output[drug] = {
            **info,
            'national_claims_pct': round(
                national_weights.get(drug, 0) * 100, 1,
            ),
        }

    # Per-state weighted loss
    per_state = {}
    for state, weights in state_weights.items():
        state_loss = 0.0
        dominant_drug = ''
        dominant_pct = 0.0
        for drug, weight in weights.items():
            loss = per_drug_loss.get(drug, {}).get(
                'structural_loss_per_fill', 0,
            )
            state_loss += loss * weight
            if weight > dominant_pct:
                dominant_pct = weight
                dominant_drug = drug

        per_state[state] = {
            'weighted_loss_per_fill': round(state_loss, 2),
            'dominant_drug': dominant_drug,
            'dominant_drug_pct': round(dominant_pct * 100, 1),
        }

    # Assemble output
    output = {
        'national_weighted_loss_per_fill': round(national_loss, 2),
        'methodology': (
            'Structural loss = NADAC acquisition cost - PBM reimbursement. '
            f'PBMs reimburse ~{REIMBURSEMENT_RATIO * 100:.1f}% of NADAC on GLP-1s '
            f'({(1 - REIMBURSEMENT_RATIO) * 100:.1f}% underwater). '
            'Based on NCPA survey data showing $42/fill avg loss on ~$1000 '
            'acquisition (~4.2% underwater). We use conservative 3.5% estimate. '
            'Weighted by CMS Part D prescribing volume (national and '
            'per-state drug mix). NADAC source: data.medicaid.gov '
            '(weekly pharmacy acquisition costs). '
            'Note: actual pharmacy acquisition costs vary by wholesaler '
            'contract, GPO membership, and volume. NADAC is a national '
            'average. Reimbursement varies by PBM contract.'
        ),
        'data_sources': {
            'nadac': 'data.medicaid.gov NADAC (National Average Drug Acquisition Cost)',
            'prescribing_volume': 'CMS Part D Prescribers by Provider and Drug',
            'reimbursement_ratio': REIMBURSEMENT_RATIO,
            'underwater_pct': f'{(1 - REIMBURSEMENT_RATIO) * 100:.1f}%',
        },
        'per_drug': per_drug_output,
        'per_state': dict(sorted(per_state.items())),
    }

    return output


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Compute GLP-1 loss per fill from NADAC',
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Force re-download NADAC data',
    )
    args = parser.parse_args()

    # Step 1: Download NADAC prices
    nadac_prices = download_nadac_glp1(force=args.force)
    if not nadac_prices:
        print("ERROR: No NADAC prices downloaded.")
        sys.exit(1)

    # Step 2: Compute per-drug structural loss
    per_drug_loss = compute_loss_per_drug(nadac_prices)

    print("\nPer-drug structural loss:")
    for drug, info in sorted(per_drug_loss.items()):
        print(f"  {drug}: "
              f"acquisition ${info['acquisition_per_fill']:.2f}, "
              f"reimbursement ${info['est_reimbursement_per_fill']:.2f}, "
              f"loss ${info['structural_loss_per_fill']:.2f}")

    # Step 3: Load drug mix weights
    national_weights, state_weights = load_drug_mix()

    print("\nNational drug mix weights:")
    for drug, w in sorted(national_weights.items()):
        print(f"  {drug}: {w * 100:.1f}%")

    # Step 4: Compute weighted loss
    output = compute_weighted_loss(
        per_drug_loss, national_weights, state_weights,
    )

    print(f"\nNational weighted loss per fill: "
          f"${output['national_weighted_loss_per_fill']:.2f}")

    # Show state range
    if output['per_state']:
        state_losses = [
            v['weighted_loss_per_fill']
            for v in output['per_state'].values()
        ]
        print(f"State range: ${min(state_losses):.2f} - "
              f"${max(state_losses):.2f}")

    # Step 5: Write output
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nWrote {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
