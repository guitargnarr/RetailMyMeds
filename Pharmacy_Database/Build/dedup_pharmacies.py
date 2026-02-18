#!/usr/bin/env python3
"""
RMM Pharmacy Deduplication Pipeline
=====================================
5-stage pipeline to deduplicate and clean NPI-verified pharmacy data.

Input:  State_Outreach_Lists_Verified/ALL_VERIFIED_PHARMACIES.csv (39,611 rows)
        Pharmacy_Database/Deliverables/qualified_independent_pharmacies_feb2026.csv (addresses)
Output: State_Outreach_Lists_Verified/ALL_VERIFIED_DEDUPED.csv (34,632 rows)
        State_Outreach_Lists_Verified/ALL_VERIFIED_CLEAN.csv (33,185 rows)

Pipeline stages:
  1. Address-based dedup: normalize street addresses, group co-located NPIs,
     keep one winner per physical location (-4,979)
  2. Remove institutional: hospitals, health centers, VA, FQHCs, health systems (-711)
  3. Remove specialty/compounding taxonomy (-464)
  4. Remove chains that slipped past initial independent filter (-89)
  5. Remove non-pharmacy clinics (-183)

Background:
  Multiple NPI registrations can exist per physical pharmacy location (owner NPI +
  pharmacy NPI + DBA NPIs). Brooklyn 11220 alone had 99 NPIs. The NCPA reports
  18,984 independent pharmacies; our NPI data had 39,611. After dedup: 33,185
  (1.75x NCPA -- remaining gap is definitional: NCPA surveys members and counts
  storefronts; NPI data includes every registered pharmacy entity).

Note on reproducibility:
  The original dedup was run as inline Python in a conversation session (Feb 18, 2026).
  This script reconstructs that logic from the methodology and results. The keyword
  lists for stages 2-5 are documented best-effort approximations. The committed CSV
  files (ALL_VERIFIED_DEDUPED.csv, ALL_VERIFIED_CLEAN.csv) remain the authoritative
  outputs. Running this script will produce slightly different counts due to keyword
  coverage differences. The scoring engine (score_pharmacies.py) reproduces exact
  scores when run on the committed clean file.

Usage:
  python3 dedup_pharmacies.py
  python3 dedup_pharmacies.py --verified /path/to/verified.csv --qualified /path/to/qualified.csv
"""

import csv
import os
import re
import sys
import argparse
from pathlib import Path
from collections import Counter, defaultdict


# --- Stage 1: Address Normalization and Dedup ---

# Suite/unit patterns to strip
SUITE_PATTERN = re.compile(
    r'\b(STE|SUITE|UNIT|APT|APARTMENT|RM|ROOM|FL|FLOOR|BLDG|BUILDING|#)\s*\.?\s*\w*\s*$',
    re.IGNORECASE
)

# Address abbreviation normalization
ABBREV_MAP = {
    'STREET': 'ST', 'AVENUE': 'AVE', 'BOULEVARD': 'BLVD', 'DRIVE': 'DR',
    'ROAD': 'RD', 'LANE': 'LN', 'COURT': 'CT', 'PLACE': 'PL',
    'CIRCLE': 'CIR', 'HIGHWAY': 'HWY', 'PARKWAY': 'PKWY', 'TERRACE': 'TER',
    'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W',
    'NORTHWEST': 'NW', 'NORTHEAST': 'NE', 'SOUTHWEST': 'SW', 'SOUTHEAST': 'SE',
}


def normalize_address(addr):
    """Normalize a street address for dedup grouping."""
    if not addr:
        return ''
    addr = addr.upper().strip()
    # Strip suite/unit suffixes
    addr = SUITE_PATTERN.sub('', addr).strip()
    addr = addr.rstrip(',').strip()
    # Standardize abbreviations
    words = addr.split()
    words = [ABBREV_MAP.get(w.rstrip('.'), w.rstrip('.')) for w in words]
    return ' '.join(words)


def pick_winner(group):
    """Pick the best NPI from a group of co-located pharmacies.

    Priority: owner-priority NPIs first, then longer names (more specific),
    then lowest NPI (oldest registration).
    """
    def sort_key(r):
        name = r.get('display_name', '') or ''
        owner = r.get('owner_name', '') or ''
        # Prefer entries with owner info
        has_owner = 1 if owner.strip() else 0
        return (-has_owner, -len(name), r.get('npi', ''))

    return sorted(group, key=sort_key)[0]


def stage1_address_dedup(verified_rows, qualified_rows):
    """Deduplicate by normalized street address + city + state + zip."""
    # Build address lookup from qualified file (has street addresses)
    addr_by_npi = {}
    for r in qualified_rows:
        addr_by_npi[r['npi']] = {
            'address_1': r.get('address_1', ''),
            'address_2': r.get('address_2', ''),
        }

    # Group by normalized location
    groups = defaultdict(list)
    no_address = []
    for r in verified_rows:
        addr_info = addr_by_npi.get(r['npi'])
        if not addr_info or not addr_info['address_1'].strip():
            no_address.append(r)
            continue

        norm_addr = normalize_address(addr_info['address_1'])
        city = (r.get('city', '') or '').upper().strip()
        state = (r.get('state', '') or '').upper().strip()
        zip5 = (r.get('zip', '') or '').strip()[:5]

        key = (norm_addr, city, state, zip5)
        groups[key].append(r)

    # Pick winner per group
    deduped = []
    for key, group in groups.items():
        deduped.append(pick_winner(group))

    # Add back any without addresses (keep them)
    deduped.extend(no_address)

    # Sort by state, city, name for consistent output
    deduped.sort(key=lambda r: (r.get('state', ''), r.get('city', ''), r.get('display_name', '')))

    return deduped


# --- Stage 2: Institutional Removal ---

INSTITUTIONAL_KEYWORDS = [
    'HOSPITAL', 'MEDICAL CENTER', 'HEALTH CENTER', 'HEALTH CENTRES',
    'VA MEDICAL', 'VA HEALTH', 'VETERANS AFFAIRS', 'VETERANS ADMIN',
    'FQHC', 'COMMUNITY HEALTH', 'NEIGHBORHOOD HEALTH',
    'INDIAN HEALTH SERVICE', 'IHS ',
    'HEALTH SYSTEM', 'HEALTH CARE SERVICES', 'HEALTHCARE SYSTEM',
    'BEHAVIORAL HEALTH', 'MENTAL HEALTH',
    'REHABILITATION CENTER', 'REHAB CENTER',
    'NURSING HOME', 'NURSING FACILITY',
    'CORRECTIONAL', 'DETENTION',
    'ONCOLOGY PHARMACY SERVICE', 'INFUSION CENTER',
    'FAMILY HEALTH CENTER', 'RURAL HEALTH',
    'FARM WORKERS CLINIC', 'MIGRANT HEALTH',
    'CLINICA SIERRA VISTA', 'CLINICA DE SALUD',
    'NYU LANGONE', 'CLEVELAND CLINIC', 'GEISINGER CLINIC',
    'MAYO CLINIC', 'CEDARS-SINAI',
    'SETON FAMILY OF', 'SENTARA ', 'NORTON HOSPITALS',
    'INOVA HEALTH', 'MULTICARE HEALTH',
    'METROHEALTH', 'LOVELACE HEALTH',
    'DULUTH CLINIC', 'MARSHFIELD CLINIC',
    'SEA MAR COMMUNITY', 'REGENESIS',
    'LEON MEDICAL CENTER', 'SUN LIFE FAMILY',
    'KATAHDIN VALLEY', 'CANYONLANDS COMMUNITY',
    'ADVANCE COMMUNITY HEALTH',
    'PHARMACY4HUMANITY',
    'EL RIO SANTA CRUZ', 'PENOBSCOT COMMUNITY',
    'WINN COMMUNITY HEALTH', 'MOREHOUSE COMMUNITY',
    'STEPHEN F AUSTIN COMMUNITY', 'CAN COMMUNITY HEALTH',
    'HEART OF FLORIDA HEALTH', 'GULF HEALTH',
    'TAMPA FAMILY HEALTH', 'GREATER LAWRENCE FAMILY HEALTH',
    'ST. JOHN\'S COMMUNITY HEALTH', 'CHEROKEE HEALTH',
]


def _get_name(r):
    """Get uppercased display name from a row."""
    return (r.get('display_name', '') or '').upper()


def _has_keyword(r, keywords):
    """Check if row's display name contains any keyword."""
    name = _get_name(r)
    return any(kw in name for kw in keywords)


def stage2_remove_institutional(rows):
    """Remove hospitals, health centers, VA facilities, FQHCs, health systems."""
    return [r for r in rows if not _has_keyword(r, INSTITUTIONAL_KEYWORDS)]


# --- Stage 3: Specialty Taxonomy Removal ---

SPECIALTY_TAXONOMIES = [
    'Compounding Pharmacy',
    'Nuclear Pharmacy',
    'Specialty Pharmacy',
    'Home Infusion Therapy Pharmacy',
    'Long Term Care Pharmacy',
]


def stage3_remove_specialty(rows):
    """Remove pharmacies with specialty/compounding taxonomy codes."""
    def has_specialty(r):
        tax = r.get('primary_taxonomy_desc', '') or ''
        return any(t in tax for t in SPECIALTY_TAXONOMIES)
    return [r for r in rows if not has_specialty(r)]


# --- Stage 4: Chain Removal ---

CHAIN_KEYWORDS = [
    'CVS', 'WALGREENS', 'WALMART', 'RITE AID', 'RITE-AID',
    'COSTCO', 'KROGER', 'PUBLIX', 'H-E-B', 'HEB ',
    'ALBERTSONS', 'SAFEWAY', 'SUPERMARKET',
    'ROSAUERS', 'WINN-DIXIE', 'WINN DIXIE',
    'HAGGEN', 'APEX DRUG STORES', 'PDS I MICHIGAN',
    'K & B MISSISSIPPI',
]

CONVENIENCE_KEYWORDS = [
    'KWICKMART', 'KWIKMART', 'QUICKMART', 'FRANKMART',
]


def stage4_remove_chains(rows):
    """Remove chain pharmacies and convenience store pharmacies."""
    all_kw = CHAIN_KEYWORDS + CONVENIENCE_KEYWORDS
    return [r for r in rows if not _has_keyword(r, all_kw)]


# --- Stage 5: Non-Pharmacy Clinic Removal ---

CLINIC_KEYWORDS = [
    'CLINIC,', 'CLINIC ', 'CLINICS,', 'CLINICS ',
    'MEDICAL GROUP', 'PHYSICIANS GROUP',
    'ASSOCIATES MD', 'ASSOCIATES, MD',
    'FAMILY PRACTICE', 'FAMILY MEDICINE',
    'PEDIATRIC', 'URGENT CARE',
    'INTERNAL MEDICINE', 'PRIMARY CARE',
    'IHS PHARMACY', 'IREDELL',
]


def stage5_remove_clinics(rows):
    """Remove non-pharmacy clinic entities."""
    return [r for r in rows if not _has_keyword(r, CLINIC_KEYWORDS)]


# --- Main ---

def dedup_pharmacies(verified_path, qualified_path, output_dir):
    """Run full 5-stage dedup pipeline."""

    # Read inputs
    with open(verified_path, 'r') as f:
        verified = list(csv.DictReader(f))
    with open(qualified_path, 'r') as f:
        qualified = list(csv.DictReader(f))

    print(f"Input: {len(verified):,} verified pharmacies")
    print(f"Address source: {len(qualified):,} qualified pharmacies")

    # Stage 1: Address dedup
    stage1 = stage1_address_dedup(verified, qualified)
    s1_removed = len(verified) - len(stage1)
    print(f"\nStage 1 (address dedup): {len(verified):,} -> {len(stage1):,} (-{s1_removed:,})")

    # Write deduped intermediate
    deduped_path = os.path.join(output_dir, 'ALL_VERIFIED_DEDUPED.csv')
    fieldnames = verified[0].keys()
    with open(deduped_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stage1)
    print(f"  Wrote {deduped_path}")

    # Stage 2: Remove institutional
    stage2 = stage2_remove_institutional(stage1)
    s2_removed = len(stage1) - len(stage2)
    print(f"\nStage 2 (institutional): {len(stage1):,} -> {len(stage2):,} (-{s2_removed:,})")

    # Stage 3: Remove specialty taxonomy
    stage3 = stage3_remove_specialty(stage2)
    s3_removed = len(stage2) - len(stage3)
    print(f"Stage 3 (specialty/compounding): {len(stage2):,} -> {len(stage3):,} (-{s3_removed:,})")

    # Stage 4: Remove chains
    stage4 = stage4_remove_chains(stage3)
    s4_removed = len(stage3) - len(stage4)
    print(f"Stage 4 (chains): {len(stage3):,} -> {len(stage4):,} (-{s4_removed:,})")

    # Stage 5: Remove clinics
    stage5 = stage5_remove_clinics(stage4)
    s5_removed = len(stage4) - len(stage5)
    print(f"Stage 5 (clinics): {len(stage4):,} -> {len(stage5):,} (-{s5_removed:,})")

    # Write clean output
    clean_path = os.path.join(output_dir, 'ALL_VERIFIED_CLEAN.csv')
    with open(clean_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stage5)
    print(f"\nWrote {clean_path}")

    # Summary stats
    print("\n--- Summary ---")
    print(f"Original:  {len(verified):>7,}")
    removed_dedup = len(verified) - len(stage1)
    removed_clean = len(stage1) - len(stage5)
    print(f"Deduped:   {len(stage1):>7,}  (-{removed_dedup:,} address duplicates)")
    print(f"Clean:     {len(stage5):>7,}  (-{removed_clean:,} non-independent)")
    print("NCPA ref:   18,984")
    ratio = len(stage5) / 18984
    print(f"Ratio:     {ratio:.2f}x NCPA")

    # State distribution
    states = Counter(r.get('state', '') for r in stage5)
    print("\nTop 10 states:")
    for st, cnt in states.most_common(10):
        print(f"  {st}: {cnt:,}")

    return stage5


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RMM Pharmacy Dedup Pipeline')
    parser.add_argument('--verified', default=None, help='Path to verified pharmacies CSV')
    parser.add_argument('--qualified', default=None, help='Path to qualified pharmacies CSV (for addresses)')
    parser.add_argument('--output-dir', default=None, help='Output directory')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    verified_path = args.verified or repo_root / 'State_Outreach_Lists_Verified' / 'ALL_VERIFIED_PHARMACIES.csv'
    qualified_path = (
        args.qualified
        or repo_root / 'Pharmacy_Database' / 'Deliverables'
        / 'qualified_independent_pharmacies_feb2026.csv'
    )
    output_dir = args.output_dir or repo_root / 'State_Outreach_Lists_Verified'

    if not os.path.exists(verified_path):
        print(f"ERROR: Verified file not found: {verified_path}")
        sys.exit(1)
    if not os.path.exists(qualified_path):
        print(f"ERROR: Qualified file not found: {qualified_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    dedup_pharmacies(str(verified_path), str(qualified_path), str(output_dir))
