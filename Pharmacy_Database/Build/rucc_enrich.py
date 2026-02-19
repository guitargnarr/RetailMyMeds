#!/usr/bin/env python3
"""
RUCC Enrichment Module
=======================
Maps 5-digit ZIP codes to USDA Rural-Urban Continuum Codes via county FIPS.

Data sources (public, no login required):
  - USDA RUCC 2023: county-level rural/urban classification (1-9 scale)
  - Census ZCTA-to-County crosswalk: maps ZIP codes to counties

Classification:
  Metro          = RUCC 1-3
  Rural-Adjacent = RUCC 4, 6, 8  (nonmetro, adjacent to metro)
  Rural-Remote   = RUCC 5, 7, 9  (nonmetro, not adjacent to metro)

Usage:
  from rucc_enrich import build_zip_lookup
  lookup = build_zip_lookup()
  info = lookup.get('40422', {})
  # {'county_fips': '21053', 'county_name': 'Clinton County',
  #  'rucc_code': 7, 'rural_classification': 'Rural-Remote'}
"""

import csv
import os
import urllib.request
from pathlib import Path


# --- Configuration ---

RUCC_URL = (
    'https://www.ers.usda.gov/media/5768/'
    '2023-rural-urban-continuum-codes.csv'
)
ZCTA_URL = (
    'https://www2.census.gov/geo/docs/maps-data/data/rel2020/'
    'zcta520/tab20_zcta520_county20_natl.txt'
)

REFERENCE_DIR = Path(__file__).resolve().parent / 'reference_data'
RUCC_CACHE = REFERENCE_DIR / 'rucc_2023.csv'
ZCTA_CACHE = REFERENCE_DIR / 'zcta_county_crosswalk.txt'

RUCC_CLASSIFICATION: dict[int, str] = {
    1: 'Metro', 2: 'Metro', 3: 'Metro',
    4: 'Rural-Adjacent', 5: 'Rural-Remote',
    6: 'Rural-Adjacent', 7: 'Rural-Remote',
    8: 'Rural-Adjacent', 9: 'Rural-Remote',
}


# --- Download helpers ---

def download_rucc(force: bool = False) -> Path:
    """Download USDA RUCC 2023 CSV if not cached."""
    if RUCC_CACHE.exists() and not force:
        return RUCC_CACHE
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    print(f"Downloading RUCC 2023 from {RUCC_URL}...")
    urllib.request.urlretrieve(RUCC_URL, RUCC_CACHE)
    print(f"  Saved to {RUCC_CACHE}")
    return RUCC_CACHE


def download_zcta_crosswalk(force: bool = False) -> Path:
    """Download Census ZCTA-to-County crosswalk if not cached."""
    if ZCTA_CACHE.exists() and not force:
        return ZCTA_CACHE
    os.makedirs(REFERENCE_DIR, exist_ok=True)
    print(f"Downloading ZCTA crosswalk from {ZCTA_URL}...")
    urllib.request.urlretrieve(ZCTA_URL, ZCTA_CACHE)
    print(f"  Saved to {ZCTA_CACHE}")
    return ZCTA_CACHE


# --- Lookup construction ---

RuccInfo = dict[str, object]


def _load_rucc() -> dict[str, tuple[str, int]]:
    """Load RUCC codes by county FIPS.

    Returns dict mapping FIPS -> (county_name, rucc_code).
    """
    rucc_path = download_rucc()
    result: dict[str, tuple[str, int]] = {}
    with open(rucc_path, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Attribute'] == 'RUCC_2023':
                fips = row['FIPS'].zfill(5)
                code = int(row['Value'])
                name = row['County_Name']
                result[fips] = (name, code)
    return result


def _load_zcta_to_county() -> dict[str, str]:
    """Map each ZCTA to its dominant county FIPS (by land area).

    Returns dict mapping ZIP5 -> county FIPS (5-digit, zero-padded).
    """
    zcta_path = download_zcta_crosswalk()
    # Track best (largest land area) county per ZCTA
    best: dict[str, tuple[str, int]] = {}  # zip -> (fips, area)
    with open(zcta_path, 'r', encoding='utf-8-sig') as f:
        header = f.readline().strip().split('|')
        zcta_idx = header.index('GEOID_ZCTA5_20')
        county_idx = header.index('GEOID_COUNTY_20')
        area_idx = header.index('AREALAND_PART')
        for line in f:
            parts = line.strip().split('|')
            zcta = parts[zcta_idx].strip()
            if not zcta:
                continue
            county_fips = parts[county_idx].strip()
            try:
                area = int(parts[area_idx])
            except (ValueError, IndexError):
                area = 0
            if zcta not in best or area > best[zcta][1]:
                best[zcta] = (county_fips, area)
    return {z: fips for z, (fips, _) in best.items()}


def build_zip_lookup() -> dict[str, RuccInfo]:
    """Build ZIP -> RUCC info lookup.

    Returns dict mapping ZIP5 -> {
        'county_fips': str,
        'county_name': str,
        'rucc_code': int,
        'rural_classification': str
    }

    ZIPs without a match return empty dict on .get().
    """
    rucc_by_fips = _load_rucc()
    zip_to_county = _load_zcta_to_county()

    lookup: dict[str, RuccInfo] = {}
    matched = 0
    for zip5, county_fips in zip_to_county.items():
        if county_fips in rucc_by_fips:
            county_name, rucc_code = rucc_by_fips[county_fips]
            classification = RUCC_CLASSIFICATION.get(
                rucc_code, 'Unknown'
            )
            lookup[zip5] = {
                'county_fips': county_fips,
                'county_name': county_name,
                'rucc_code': rucc_code,
                'rural_classification': classification,
            }
            matched += 1

    total_zips = len(zip_to_county)
    pct = matched / total_zips * 100
    print(f"RUCC lookup: {matched:,}/{total_zips:,} ZIPs mapped "
          f"({pct:.1f}%)")
    print(f"  Counties with RUCC: {len(rucc_by_fips):,}")

    return lookup


if __name__ == '__main__':
    lookup = build_zip_lookup()
    print(f"\nTotal ZIPs in lookup: {len(lookup):,}")

    # Spot checks
    for test_zip in ['40422', '10001', '90210', '00601']:
        info = lookup.get(test_zip, {})
        if info:
            print(f"  {test_zip}: {info['county_name']} "
                  f"(FIPS {info['county_fips']}) "
                  f"RUCC {info['rucc_code']} = "
                  f"{info['rural_classification']}")
        else:
            print(f"  {test_zip}: no match")
