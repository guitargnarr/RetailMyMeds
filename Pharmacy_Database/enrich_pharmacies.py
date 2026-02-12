#!/usr/bin/env python3
"""
Enrich Independent Pharmacy Database
=====================================
Takes the base independent_pharmacies_usa_feb2026.csv and adds:
1. estimated_status  - Active/Likely Active/Uncertain/Likely Closed
2. owner_name        - From NPPES Authorized Official fields
3. owner_title       - From NPPES Authorized Official fields
4. owner_phone       - From NPPES Authorized Official fields

NOTE on Rx volume and GLP-1 data:
CMS Part D public use files (Prescriber PUF, Prescriber by Drug) are keyed
to PRESCRIBER NPIs (doctors), not PHARMACY/DISPENSER NPIs. Pharmacy-level
dispensing data lives in the Part D Event (PDE) files, which require a
formal CMS Data Use Agreement. There is no free public download of
pharmacy-level claim counts or drug-specific dispensing volumes.

The enrichment columns for Rx volume and GLP-1 dispensing will require
either: (a) NCPDP DataQ subscription, or (b) CMS PDE Data Use Agreement.

Output: qualified_independent_pharmacies_feb2026.csv
"""

import csv
import os
import zipfile
import glob
from datetime import datetime


BASE_DIR = '/Users/matthewscott/Desktop/RetailMyMeds/Pharmacy_Database'
INPUT_CSV = os.path.join(BASE_DIR, 'independent_pharmacies_usa_feb2026.csv')
OUTPUT_CSV = os.path.join(BASE_DIR, 'qualified_independent_pharmacies_feb2026.csv')
NPPES_ZIP = os.path.join(BASE_DIR, 'nppes_feb2026.zip')


def compute_status(last_updated_str):
    """Compute estimated operating status from last_updated date."""
    if not last_updated_str:
        return 'Likely Closed'
    try:
        year = int(last_updated_str.split('/')[-1])
    except (ValueError, IndexError):
        return 'Likely Closed'

    if year >= 2024:
        return 'Active'
    elif year >= 2020:
        return 'Likely Active'
    elif year >= 2015:
        return 'Uncertain'
    else:
        return 'Likely Closed'


def load_base_pharmacies():
    """Load the existing independent pharmacy CSV into a dict keyed by NPI."""
    print(f"[{now()}] Loading base pharmacy file...")
    pharmacies = {}
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            npi = row['npi'].strip()
            pharmacies[npi] = row
    print(f"  Loaded {len(pharmacies):,} pharmacies")
    return pharmacies


def enrich_status(pharmacies):
    """Add estimated_status column based on last_updated."""
    print(f"\n[{now()}] Enrichment 1: Computing estimated_status...")
    counts = {}
    for npi, p in pharmacies.items():
        status = compute_status(p.get('last_updated', ''))
        p['estimated_status'] = status
        counts[status] = counts.get(status, 0) + 1

    for status in ['Active', 'Likely Active', 'Uncertain', 'Likely Closed']:
        print(f"  {status}: {counts.get(status, 0):,}")


def enrich_owner_info(pharmacies):
    """Extract Authorized Official fields from NPPES bulk file."""
    print(f"\n[{now()}] Enrichment 2: Extracting owner info from NPPES...")

    if not os.path.exists(NPPES_ZIP):
        print("  WARNING: NPPES ZIP not found. Skipping owner enrichment.")
        for p in pharmacies.values():
            p['owner_name'] = ''
            p['owner_title'] = ''
            p['owner_phone'] = ''
        return

    extract_dir = os.path.join(BASE_DIR, 'nppes_extracted')
    if not os.path.exists(extract_dir):
        print("  Extracting ZIP...")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(NPPES_ZIP, 'r') as zf:
            zf.extractall(extract_dir)
        print("  Extraction complete.")
    else:
        print("  Using previously extracted files")

    csv_path = find_nppes_csv(extract_dir)
    if not csv_path:
        print("  ERROR: Could not find NPPES CSV!")
        for p in pharmacies.values():
            p['owner_name'] = ''
            p['owner_title'] = ''
            p['owner_phone'] = ''
        return

    print(f"  Scanning {os.path.basename(csv_path)} for owner data...")
    npi_set = set(pharmacies.keys())
    matched = 0
    total = 0

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if total % 1_000_000 == 0:
                print(f"  [{now()}] Scanned {total:,} rows..."
                      f" ({matched:,} matched)")

            npi = row.get('NPI', '').strip()
            if npi not in npi_set:
                continue

            first = row.get('Authorized Official First Name', '').strip()
            last = row.get('Authorized Official Last Name', '').strip()
            title = row.get(
                'Authorized Official Title or Position', ''
            ).strip()
            phone = row.get(
                'Authorized Official Telephone Number', ''
            ).strip()

            if first or last:
                name = f"{first} {last}".strip()
            else:
                name = ''

            pharmacies[npi]['owner_name'] = name
            pharmacies[npi]['owner_title'] = title
            pharmacies[npi]['owner_phone'] = phone
            matched += 1

    # Fill blanks for any unmatched
    for p in pharmacies.values():
        if 'owner_name' not in p:
            p['owner_name'] = ''
            p['owner_title'] = ''
            p['owner_phone'] = ''

    print(f"  Owner info matched: {matched:,} / {len(pharmacies):,}")


def find_nppes_csv(extract_dir):
    """Find the main NPPES CSV file in the extracted directory."""
    patterns = [
        os.path.join(extract_dir, 'npidata_pfile_*.csv'),
        os.path.join(
            extract_dir,
            'NPPES_Data_Dissemination_*',
            'npidata_pfile_*.csv',
        ),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            matches.sort(
                key=lambda f: os.path.getsize(f), reverse=True
            )
            return matches[0]
    for f in glob.glob(
        os.path.join(extract_dir, '**', '*.csv'), recursive=True
    ):
        size = os.path.getsize(f)
        if size > 1_000_000_000:
            return f
    return None


def write_output(pharmacies):
    """Write the final qualified CSV."""
    print(f"\n[{now()}] Writing qualified output...")

    fieldnames = [
        'npi', 'display_name', 'legal_name', 'dba_name',
        'address_1', 'address_2', 'city', 'state', 'zip', 'phone',
        'enumeration_date', 'last_updated',
        'estimated_status',
        'owner_name', 'owner_title', 'owner_phone',
    ]

    # Sort: Active first, then by state, city, name
    status_order = {
        'Active': 0, 'Likely Active': 1,
        'Uncertain': 2, 'Likely Closed': 3,
    }
    records = sorted(
        pharmacies.values(),
        key=lambda x: (
            status_order.get(x.get('estimated_status', ''), 9),
            x.get('state', ''),
            x.get('city', ''),
            x.get('display_name', ''),
        )
    )

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, extrasaction='ignore'
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"  Output: {OUTPUT_CSV}")
    print(f"  Records: {len(records):,}")

    # Summary stats
    status_counts = {}
    has_owner = 0
    for r in records:
        st = r.get('estimated_status', '')
        status_counts[st] = status_counts.get(st, 0) + 1
        if r.get('owner_name', '').strip():
            has_owner += 1

    print("\n  Summary:")
    print(f"  {'Status':<20} {'Count':>8}")
    print("  " + "-" * 30)
    for status in ['Active', 'Likely Active', 'Uncertain', 'Likely Closed']:
        print(f"  {status:<20} {status_counts.get(status, 0):>8,}")
    print("  " + "-" * 30)
    print(f"  {'Total':<20} {len(records):>8,}")
    print(f"  {'With owner name':<20} {has_owner:>8,}")

    # Owner name coverage by status
    print("\n  Owner coverage by status:")
    for status in ['Active', 'Likely Active', 'Uncertain', 'Likely Closed']:
        total_st = status_counts.get(status, 0)
        with_owner = sum(
            1 for r in records
            if r.get('estimated_status') == status
            and r.get('owner_name', '').strip()
        )
        pct = (with_owner / total_st * 100) if total_st else 0
        print(f"  {status:<20} {with_owner:>6,} / {total_st:>6,}"
              f" ({pct:.1f}%)")


def now():
    return datetime.now().strftime('%H:%M:%S')


if __name__ == '__main__':
    print(f"[{now()}] Starting pharmacy enrichment pipeline...")
    print(f"  Input: {INPUT_CSV}")
    print(f"  Output: {OUTPUT_CSV}")

    pharmacies = load_base_pharmacies()
    enrich_status(pharmacies)
    enrich_owner_info(pharmacies)
    write_output(pharmacies)

    print(f"\n[{now()}] Enrichment complete.")
