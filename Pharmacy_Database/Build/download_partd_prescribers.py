#!/usr/bin/env python3
"""
Download and Filter CMS Part D Prescribers by Provider and Drug
================================================================
Downloads the full Part D CSV (~5GB) via streaming, filters for GLP-1
drugs line-by-line (never loads full file into memory), and produces
ZIP-level + state drug-mix aggregations.

Also downloads the Geography+Drug dataset (state-level, much smaller)
via the CMS REST API for state-level drug mix weights.

Data sources (public, no login):
  CSV: data.cms.gov/sites/default/files/.../MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv
  API: data.cms.gov/data-api/v1/dataset/{uuid}/data (Geography+Drug)

Output:
  reference_data/partd_glp1_by_zip.csv
  reference_data/partd_glp1_drug_mix.csv

Usage:
  python3 download_partd_prescribers.py
  python3 download_partd_prescribers.py --force

Dependencies: requests
"""

import argparse
import csv
import io
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. pip install requests")
    sys.exit(1)


# --- Configuration ---

REFERENCE_DIR = Path(__file__).resolve().parent / 'reference_data'

# Full CSV download (2023 data, latest)
CSV_URL = (
    'https://data.cms.gov/sites/default/files/2025-04/'
    '0d5915ce-002c-4d87-bde8-24ffb08bb6cc/'
    'MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv'
)

# Geography+Drug API (state-level, small dataset)
GEO_DRUG_API = (
    'https://data.cms.gov/data-api/v1/dataset/'
    '3463648b-1971-478d-84ca-80cadc758153/data'
)

GLP1_GENERICS = {
    'semaglutide', 'tirzepatide', 'liraglutide',
    'dulaglutide', 'exenatide',
}

GLP1_BRANDS_UPPER = {
    'OZEMPIC', 'WEGOVY', 'RYBELSUS',
    'MOUNJARO', 'ZEPBOUND',
    'VICTOZA', 'SAXENDA',
    'TRULICITY',
    'BYETTA', 'BYDUREON',
}

ZIP_OUTPUT = REFERENCE_DIR / 'partd_glp1_by_zip.csv'
DRUG_MIX_OUTPUT = REFERENCE_DIR / 'partd_glp1_drug_mix.csv'
RAW_CACHE = REFERENCE_DIR / 'partd_glp1_raw_cache.csv'
GEO_CACHE = REFERENCE_DIR / 'partd_glp1_geo_cache.json'


def _drug_key(generic_name: str) -> str:
    gn = generic_name.strip().lower()
    for drug in GLP1_GENERICS:
        if drug in gn:
            return drug
    return ''


def _is_glp1(gnrc_name: str, brnd_name: str) -> bool:
    """Fast check if a record is a GLP-1 drug."""
    gn = gnrc_name.strip().lower()
    for drug in GLP1_GENERICS:
        if drug in gn:
            return True
    bn = brnd_name.strip().upper()
    for brand in GLP1_BRANDS_UPPER:
        if brand in bn:
            return True
    return False


# --- City-to-ZIP lookup ---

def _build_city_state_to_zip() -> dict[str, str]:
    """Build city+state -> ZIP lookup from our pharmacy database."""
    # Script: RetailMyMeds/Pharmacy_Database/Build/ -> parent^3 = RetailMyMeds/
    rmm_root = Path(__file__).resolve().parent.parent.parent
    clean_csv = rmm_root / 'State_Outreach_Lists_Verified' / 'ALL_VERIFIED_CLEAN.csv'

    city_zip: dict[str, str] = {}
    if clean_csv.exists():
        with open(clean_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = row.get('city', '').strip().upper()
                state = row.get('state', '').strip().upper()
                zip5 = str(row.get('zip', '')).strip()[:5]
                if city and state and zip5:
                    key = f"{city}|{state}"
                    if key not in city_zip:
                        city_zip[key] = zip5

    print(f"  City->ZIP lookup: {len(city_zip):,} city-state pairs")
    return city_zip


# --- Streaming CSV download + filter ---

def download_and_filter_csv(force: bool = False) -> list[dict]:
    """Stream-download the full Part D CSV and filter for GLP-1 drugs.

    Streams line-by-line so we never hold 5GB in memory.
    Caches the filtered GLP-1 records (~50-100K rows) to a local CSV.
    """
    if RAW_CACHE.exists() and not force:
        print(f"Loading cached GLP-1 records from {RAW_CACHE}")
        records = []
        with open(RAW_CACHE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        print(f"  {len(records):,} records from cache")
        return records

    os.makedirs(REFERENCE_DIR, exist_ok=True)
    print(f"Streaming Part D CSV from CMS (~5GB)...")
    print(f"  URL: {CSV_URL}")

    resp = requests.get(CSV_URL, stream=True, timeout=60)
    resp.raise_for_status()

    total_size = int(resp.headers.get('content-length', 0))
    if total_size:
        print(f"  File size: {total_size / 1e9:.1f} GB")

    # Stream through the response, parse CSV line-by-line
    glp1_records = []
    header = None
    lines_processed = 0
    bytes_processed = 0
    last_report = time.time()

    # Buffer for incomplete lines
    line_buffer = ''

    for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
        if not chunk:
            continue

        bytes_processed += len(chunk)
        text = line_buffer + chunk.decode('utf-8', errors='replace')
        lines = text.split('\n')

        # Last element may be incomplete -- save for next chunk
        line_buffer = lines[-1]
        lines = lines[:-1]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if header is None:
                header = line.split(',')
                # Find column indices
                col_map = {col: i for i, col in enumerate(header)}
                gnrc_idx = col_map.get('Gnrc_Name', -1)
                brnd_idx = col_map.get('Brnd_Name', -1)
                if gnrc_idx == -1:
                    print(f"  ERROR: Gnrc_Name column not found. Columns: {header}")
                    resp.close()
                    sys.exit(1)
                continue

            lines_processed += 1

            # Fast pre-filter: check if line contains any GLP-1 keyword
            line_upper = line.upper()
            has_glp1 = False
            for brand in GLP1_BRANDS_UPPER:
                if brand in line_upper:
                    has_glp1 = True
                    break
            if not has_glp1:
                for gen in GLP1_GENERICS:
                    if gen.upper() in line_upper:
                        has_glp1 = True
                        break
            if not has_glp1:
                continue

            # Parse the CSV row properly
            try:
                row_vals = next(csv.reader(io.StringIO(line)))
            except StopIteration:
                continue

            if len(row_vals) < len(header):
                continue

            gnrc = row_vals[gnrc_idx] if gnrc_idx < len(row_vals) else ''
            brnd = row_vals[brnd_idx] if brnd_idx < len(row_vals) else ''

            if _is_glp1(gnrc, brnd):
                row_dict = dict(zip(header, row_vals))
                glp1_records.append(row_dict)

            # Progress report every 30s
            now = time.time()
            if now - last_report > 30:
                pct = (bytes_processed / total_size * 100) if total_size else 0
                print(f"  {bytes_processed / 1e9:.1f} GB ({pct:.0f}%), "
                      f"{lines_processed:,} lines, "
                      f"{len(glp1_records):,} GLP-1 records", flush=True)
                last_report = now

    # Process any remaining buffer
    if line_buffer.strip() and header:
        line_upper = line_buffer.upper()
        for brand in GLP1_BRANDS_UPPER:
            if brand in line_upper:
                try:
                    row_vals = next(csv.reader(io.StringIO(line_buffer.strip())))
                    if len(row_vals) >= len(header):
                        gnrc = row_vals[gnrc_idx]
                        brnd = row_vals[brnd_idx]
                        if _is_glp1(gnrc, brnd):
                            glp1_records.append(dict(zip(header, row_vals)))
                except StopIteration:
                    pass
                break

    resp.close()

    print(f"\n  Processed {lines_processed:,} lines total")
    print(f"  Found {len(glp1_records):,} GLP-1 prescriber records")

    # Cache filtered records
    if glp1_records and header:
        with open(RAW_CACHE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(glp1_records)
        print(f"  Cached to {RAW_CACHE}")

    return glp1_records


# --- Geography+Drug download ---

def download_geo_drug(force: bool = False) -> list[dict]:
    """Download state-level drug data via CMS REST API."""
    if GEO_CACHE.exists() and not force:
        print(f"Loading cached geo data from {GEO_CACHE}")
        with open(GEO_CACHE, 'r') as f:
            records = json.load(f)
        print(f"  {len(records):,} records")
        return records

    os.makedirs(REFERENCE_DIR, exist_ok=True)
    print("\nDownloading Geography+Drug dataset...")

    keywords = [
        'Semaglutide', 'Tirzepatide', 'Liraglutide',
        'Dulaglutide', 'Exenatide',
        'Ozempic', 'Wegovy', 'Mounjaro', 'Zepbound',
        'Victoza', 'Trulicity',
    ]

    all_records = []
    seen = set()

    for kw in keywords:
        offset = 0
        while True:
            resp = requests.get(GEO_DRUG_API, params={
                'keyword': kw, 'size': 5000, 'offset': offset,
            }, timeout=60)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            for rec in batch:
                key = f"{rec.get('Prscrbr_Geo_Cd','')}|{rec.get('Gnrc_Name','')}|{rec.get('Brnd_Name','')}"
                if key not in seen:
                    seen.add(key)
                    all_records.append(rec)
            if len(batch) < 5000:
                break
            offset += 5000
            time.sleep(0.3)
        time.sleep(0.3)

    print(f"  {len(all_records):,} geo+drug records")
    with open(GEO_CACHE, 'w') as f:
        json.dump(all_records, f)
    return all_records


# --- Aggregation ---

def aggregate_by_zip(
    records: list[dict], city_zip: dict[str, str],
) -> None:
    """Aggregate to ZIP-level via city+state matching."""
    print("\nAggregating to ZIP level...")

    zip_data: dict[str, dict] = defaultdict(lambda: {
        'total_claims': 0, 'total_cost': 0.0,
        'total_beneficiaries': 0,
        'semaglutide_claims': 0, 'tirzepatide_claims': 0,
        'liraglutide_claims': 0, 'dulaglutide_claims': 0,
        'exenatide_claims': 0,
    })

    matched = 0
    unmatched = 0

    for rec in records:
        state = rec.get('Prscrbr_State_Abrvtn', '').strip().upper()
        city = rec.get('Prscrbr_City', '').strip().upper()
        generic = rec.get('Gnrc_Name', '')
        drug = _drug_key(generic)
        if not drug:
            continue

        try:
            claims = int(float(rec.get('Tot_Clms', 0) or 0))
            cost = float(rec.get('Tot_Drug_Cst', 0) or 0)
            benes = int(float(rec.get('Tot_Benes', 0) or 0))
        except (ValueError, TypeError):
            continue

        key = f"{city}|{state}"
        zip5 = city_zip.get(key, '')
        if not zip5:
            zip5 = f"{state}000"
            unmatched += 1
        else:
            matched += 1

        z = zip_data[zip5]
        z['total_claims'] += claims
        z['total_cost'] += cost
        z['total_beneficiaries'] += benes
        z[f'{drug}_claims'] += claims

    fieldnames = [
        'zip', 'total_claims', 'total_cost', 'total_beneficiaries',
        'semaglutide_claims', 'tirzepatide_claims', 'liraglutide_claims',
        'dulaglutide_claims', 'exenatide_claims',
    ]
    rows = sorted(
        [{'zip': z, **d} for z, d in zip_data.items()],
        key=lambda r: r['zip'],
    )
    for r in rows:
        r['total_cost'] = round(r['total_cost'], 2)

    with open(ZIP_OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total_claims = sum(z['total_claims'] for z in zip_data.values())
    print(f"  Wrote {len(rows):,} ZIP records to {ZIP_OUTPUT}")
    print(f"  City->ZIP matched: {matched:,}, state-level: {unmatched:,}")
    print(f"  Total claims: {total_claims:,}")


_FIPS_TO_STATE = {
    '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA',
    '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL',
    '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN',
    '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME',
    '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS',
    '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH',
    '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
    '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI',
    '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT',
    '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI',
    '56': 'WY',
}


def aggregate_drug_mix_by_state(geo_records: list[dict]) -> None:
    """State-level drug mix from Geography dataset."""
    print("\nAggregating state-level drug mix...")

    state_drug: dict[str, dict[str, dict]] = defaultdict(
        lambda: defaultdict(lambda: {'claims': 0, 'cost': 0.0})
    )
    state_totals: dict[str, int] = defaultdict(int)

    for rec in geo_records:
        if rec.get('Prscrbr_Geo_Lvl', '').strip() != 'State':
            continue
        fips = rec.get('Prscrbr_Geo_Cd', '').strip()
        state = _FIPS_TO_STATE.get(fips.zfill(2), '')
        if not state:
            continue
        drug = _drug_key(rec.get('Gnrc_Name', ''))
        if not drug:
            continue
        try:
            claims = int(float(rec.get('Tot_Clms', 0) or 0))
            cost = float(rec.get('Tot_Drug_Cst', 0) or 0)
        except (ValueError, TypeError):
            continue
        state_drug[state][drug]['claims'] += claims
        state_drug[state][drug]['cost'] += cost
        state_totals[state] += claims

    rows = []
    for state in sorted(state_drug.keys()):
        st_total = state_totals[state]
        for drug in sorted(state_drug[state].keys()):
            d = state_drug[state][drug]
            pct = (d['claims'] / st_total * 100) if st_total else 0
            rows.append({
                'state': state, 'drug_generic': drug,
                'total_claims': d['claims'],
                'total_cost': round(d['cost'], 2),
                'pct_of_state_claims': round(pct, 1),
            })

    with open(DRUG_MIX_OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'state', 'drug_generic', 'total_claims',
            'total_cost', 'pct_of_state_claims',
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Wrote {len(rows):,} state-drug records")
    top = sorted(state_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    print("  Top 10 states:")
    for st, cnt in top:
        print(f"    {st}: {cnt:,}")


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Download CMS Part D GLP-1 prescriber data',
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Force re-download (ignore cache)',
    )
    args = parser.parse_args()

    city_zip = _build_city_state_to_zip()

    # Step 1: Stream-download full CSV, filter for GLP-1
    records = download_and_filter_csv(force=args.force)
    if not records:
        print("ERROR: No GLP-1 records found.")
        sys.exit(1)

    # Step 2: Aggregate to ZIP
    aggregate_by_zip(records, city_zip)

    # Step 3: Geography data for drug mix
    geo = download_geo_drug(force=args.force)
    if geo:
        aggregate_drug_mix_by_state(geo)
    else:
        # Fallback: drug mix from provider data
        print("\nFallback: building drug mix from provider records...")
        _fallback_drug_mix(records)

    print("\nDone.")
    print(f"  {ZIP_OUTPUT}")
    print(f"  {DRUG_MIX_OUTPUT}")


def _fallback_drug_mix(records: list[dict]) -> None:
    """Build drug mix from provider records if geo fails."""
    state_drug: dict[str, dict[str, dict]] = defaultdict(
        lambda: defaultdict(lambda: {'claims': 0, 'cost': 0.0})
    )
    state_totals: dict[str, int] = defaultdict(int)

    for rec in records:
        state = rec.get('Prscrbr_State_Abrvtn', '').strip().upper()
        drug = _drug_key(rec.get('Gnrc_Name', ''))
        if not drug or not state or len(state) != 2:
            continue
        try:
            claims = int(float(rec.get('Tot_Clms', 0) or 0))
            cost = float(rec.get('Tot_Drug_Cst', 0) or 0)
        except (ValueError, TypeError):
            continue
        state_drug[state][drug]['claims'] += claims
        state_drug[state][drug]['cost'] += cost
        state_totals[state] += claims

    rows = []
    for state in sorted(state_drug.keys()):
        st_total = state_totals[state]
        for drug in sorted(state_drug[state].keys()):
            d = state_drug[state][drug]
            pct = (d['claims'] / st_total * 100) if st_total else 0
            rows.append({
                'state': state, 'drug_generic': drug,
                'total_claims': d['claims'],
                'total_cost': round(d['cost'], 2),
                'pct_of_state_claims': round(pct, 1),
            })

    with open(DRUG_MIX_OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'state', 'drug_generic', 'total_claims',
            'total_cost', 'pct_of_state_claims',
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} state-drug records")


if __name__ == '__main__':
    main()
