#!/usr/bin/env python3
"""
Extract Independent Pharmacies from NPPES NPI Database
======================================================
Source: CMS NPPES Data Dissemination, February 9, 2026
Taxonomy: 3336C0003X (Community/Retail Pharmacy)
Entity Type: Type 2 (Organizations only)

Methodology:
1. Load full NPPES CSV (~9M records)
2. Filter to taxonomy code 3336C0003X (Community/Retail Pharmacy)
3. Filter to Entity Type Code 2 (Organizations)
4. Filter to active records only (NPI Deactivation Reason Code is blank)
5. Exclude known chain pharmacy names via pattern matching
6. Output: CSV with pharmacy name, NPI, address, city, state, zip, phone

Chain Exclusion List:
- National chains (CVS, Walgreens, Walmart, Rite Aid, etc.)
- Regional chains (HEB, Publix, Meijer, etc.)
- Grocery store pharmacies (Kroger, Safeway, Albertsons, etc.)
- Big box pharmacies (Costco, Target, etc.)
- Mail order/specialty chains
- Hospital/health system pharmacies (identified by naming patterns)
"""

import csv
import re
import os
import sys
import zipfile
import glob
from datetime import datetime

# Known chain pharmacy patterns (case-insensitive)
# These patterns match organization names that are NOT independent pharmacies
CHAIN_PATTERNS = [
    # National retail chains
    r'\bCVS\b', r'\bCARE\s*MARK\b', r'\bWALGREEN', r'\bWAL\s*MART\b', r'\bWAL-MART\b',
    r'\bSAM\'?S\s+CLUB\b', r'\bRITE\s*AID\b', r'\bRITEAID\b',
    r'\bWALGREENS?\b',

    # Grocery chains with pharmacies
    r'\bKROGER\b', r'\bALBERTSON', r'\bSAFEWAY\b', r'\bVONS\b',
    r'\bRALPH\'?S\b', r'\bFRED\s+MEYER\b', r'\bFRY\'?S\b', r'\bSMITH\'?S\b',
    r'\bQFC\b', r'\bKING\s+SOOPERS\b', r'\bDILLONS?\b', r'\bBAKER\'?S\b',
    r'\bGERBES\b', r'\bJAY\s*C\b', r'\bOWEN\'?S\b', r'\bPAY\s*LESS\b',
    r'\bPUBLIX\b', r'\bH[\-\s]*E[\-\s]*B\b', r'\bMEIJER\b',
    r'\bGIANT\s+(EAGLE|FOOD)\b', r'\bSTOP\s*&?\s*SHOP\b', r'\bSHOP\s*RITE\b',
    r'\bWEGMAN', r'\bHARRIS\s+TEETER\b', r'\bFOOD\s+LION\b',
    r'\bBI[\-\s]*LO\b', r'\bWINN[\-\s]*DIXIE\b', r'\bHARVEYS\b',
    r'\bHANNAFORD\b', r'\bPRICE\s+CHOPPER\b', r'\bHYVEE\b', r'\bHY[\-\s]VEE\b',
    r'\bSHNUCKS\b', r'\bSCHNUCKS\b', r'\bBROOKSHIRE\b',
    r'\bINGLES\b', r'\bCOBORN', r'\bCUB\s+FOOD', r'\bFARMER\s+JACK\b',
    r'\bFOOD\s+CITY\b', r'\bFOOD\s+4\s+LESS\b', r'\bFOOD\s+EMPORIUM\b',
    r'\bACME\s+MARKETS?\b', r'\bJEWEL[\-\s]OSCO\b', r'\bSTAR\s+MARKET\b',
    r'\bSHAW\'?S\b', r'\bRANDALL', r'\bTOM\s+THUMB\b',
    r'\bUNITED\s+SUPERMARKET', r'\bMARKET\s+BASKET\b', r'\bMARKET\s+STREET\b',
    r'\bSPROUTS\b', r'\bTRADER\s+JOE', r'\bWHOLE\s+FOODS\b',
    r'\bFOOD\s+FAIR\b', r'\bPIGGLY\s+WIGGLY\b',

    # Big box / warehouse
    r'\bCOSTCO\b', r'\bTARGET\b', r'\bAMAZON\b', r'\bBJ\'?S\b',

    # Department store pharmacies
    r'\bKMART\b', r'\bK[\-\s]MART\b', r'\bSEARS\b',

    # Large pharmacy chains
    r'\bEXPRESS\s+SCRIPTS\b', r'\bOPTUM\b', r'\bCARDINAL\s+HEALTH\b',
    r'\bOMNICARE\b', r'\bPHARMERICA\b', r'\bKINDRED\b',
    r'\bGENOA\b', r'\bCENTENE\b', r'\bENHALOR\b',

    # Mail order / PBM pharmacies
    r'\bMAIL\s+ORDER\b', r'\bMAIL\s+SERVICE\b', r'\bHOME\s+DELIVERY\b',

    # Regional drug store chains
    r'\bDUANE\s+READE\b', r'\bLONG\'?S\s+DRUG', r'\bBROOKS\s+PHARMACY\b',
    r'\bECKERD\b', r'\bMEDICINE\s+SHOPPE\b', r'\bGOOD\s+NEIGHBOR\b',
    r'\bHEALTH\s+MART\b',

    # Hospitals and health systems (but NOT "pharmacy at" patterns that could be independent)
    r'\bHOSPITAL\s+PHARMACY\b', r'\bMEDICAL\s+CENTER\s+PHARMACY\b',
    r'\bVA\s+MEDICAL\b', r'\bVETERANS?\s+AFFAIRS?\b', r'\bVETERANS?\s+ADMIN',
    r'\bDEPARTMENT\s+OF\s+VETERANS\b',
    r'\bINDIAN\s+HEALTH\s+SERVICE\b', r'\bTRIBAL\s+HEALTH\b',
    r'\bFEDERAL\s+BUREAU\b', r'\bARMY\b', r'\bNAVY\b', r'\bAIR\s+FORCE\b',

    # Specialty/institutional chains
    r'\bRITE\s+AID\b', r'\bCLINICAL\s+REFERENCE\b',
    r'\bCATAMARAN\b', r'\bMEDCO\b', r'\bPRIME\s+THERAPEUTICS\b',
    r'\bSCRIPT\s+PRO\b', r'\bPHARMHOUSE\b',

    # Dollar stores
    r'\bDOLLAR\s+GENERAL\b', r'\bDOLLAR\s+TREE\b',

    # Supermarket chains (additional)
    r'\bLUCKY\'?S?\s+MARKET\b', r'\bSAVE[\-\s]?MART\b', r'\bFOOD\s+MAXX\b',
    r'\bLOWES?\s+FOOD', r'\bBIG\s+Y\b', r'\bGEIST\b',
    r'\bGIANT\s+PHARMACY\b', r'\bGIANT\b(?=.*PHARMACY)',

    # Discount chains
    r'\bGOODRX\b', r'\bCAPSULE\b', r'\bALTO\s+PHARMACY\b',
    r'\bPILLPACK\b', r'\bAMAZON\s+PHARMACY\b',

    # Additional chains missed in first pass
    r'\bWALGREEN\s+CO\b', r'\bWAL-MART\s+STORES\b',
    r'\bRITE\s+AID\s+OF\b', r'\bCVS\s+STORES\b', r'\bCVS\s+PHARMACY\b',
    r'\bPUBLIX\s+SUPER\b', r'\bPUBLIX\s+TENNESSEE\b', r'\bPUBLIX\s+NORTH\b',
    r'\bPUBLIX\s+ALABAMA\b', r'\bPUBLIX\s+GEORGIA\b',
    r'\bLONGS?\s+DRUG\s+STORES?\b',
    r'\bOSCO\s+DRUG\b', r'\bJEWEL\s+FOOD\b',
    r'\bKROGER\s+LIMITED\b', r'\bTHE\s+KROGER\b',
    r'\bSAFEWAY\s+INC\b', r'\bALBERTSOMS?\b',
    r'\bWINNDIXIE\b', r'\bSAVE\s*ON\b',

    # Multi-location chains found in data audit
    r'\b1918\s+WINTER\s+STREET\b',  # Carrs/Safeway Alaska subsidiary
    r'\bSAMS\s+EAST\b', r'\bSAMS\s+WEST\b',  # Sam's Club
    r'\bHOOK[\-\s]SUPERX\b', r'\bHOOK\s+SUPERX\b',  # Kroger subsidiary
    r'\bSHOPKO\b',  # Shopko (closed chain)
    r'\bKAISER\s+FOUNDATION\b',  # Kaiser health system
    r'\bTHRIFT\s+DRUG\b',  # Rite Aid subsidiary
    r'\bAMERICAN\s+DRUG\s+STORES\b',  # Osco/Sav-on parent
    r'\bGIANT\s+OF\s+MARYLAND\b', r'\bTHE\s+GIANT\s+COMPANY\b',
    r'\bNAI\s+SATURN\b',  # Rite Aid/Revco subsidiary
    r'\bFREDS\s+STORES\b',  # Fred's (closed chain)
    r'\bGENOVESE\s+DRUG\b',  # Rite Aid subsidiary
    r'\bROUNDYS?\s+SUPERMARKET\b',  # Roundy's/Pick n Save
    r'\bAURORA\s+PHARMACY\b',  # Aurora Health System chain
    r'\bWEIS\s+MARKETS\b',  # Weis grocery chain
    r'\bKPH\s+HEALTHCARE\b',  # Kinney Drug parent
    r'\bPATHMARK\b',  # Pathmark (closed)
    r'\bDISCOUNT\s+DRUG\s+MART\b',  # Ohio chain
    r'\bSUPERVALU\b',  # Supervalu grocery
    r'\bSTOP\s+AND\s+SHOP\b',  # Stop & Shop
    r'\bTHE\s+TAMARKIN\b',  # Super X Drug/Revco
    r'\bPERRY\s+DRUG\b',  # Rite Aid subsidiary
    r'\bKERR\s+DRUG\b',  # Kerr Drug chain
    r'\bTOPS\s+MARKETS\b',  # Tops grocery
    r'\bLUCKY\s+STORES\b',  # Lucky Stores/Albertsons
    r'\bBORMANS?\b',  # Farmer Jack parent
    r'\bMARTINS?\s+FOODS?\b',  # Giant/Ahold subsidiary
    r'\bRISER\s+FOODS\b',  # Giant Eagle subsidiary
    r'\bSNYDERS?\s+DRUG\b',  # Snyder Drug chain
    r'\bRALEY',  # Raley's grocery
    r'\bMARC\s+GLASSMAN\b',  # Marc's chain
    r'\bAIDS\s+HEALTHCARE\s+FOUNDATION\b',  # AHF pharmacy chain
    r'\bMAXI\s+DRUG\b',  # Brooks/Rite Aid subsidiary
    r'\bLANE\s+DRUG\b',  # Lane Drug chain
    r'\bBARTELL\s+DRUG\b',  # Bartell Drug/Rite Aid
    r'\bBRUNO\'?S\s+SUPERMARKET\b',  # Bruno's grocery
    r'\bCENTERWELL\b',  # Humana pharmacy chain
    r'\bGOLUB\s+CORP\b',  # Price Chopper parent
    r'\bKAISER\s+FOUNDATION\s+HOSPITAL\b',
    r'\bDRUG\s+FAIR\b',  # Drug Fair chain
    r'\bHARPS\s+FOOD\b',  # Harps grocery
    r'\bGREAT\s+ATLANTIC\b', r'\bA\s*&?\s*P\s+TEA\b',  # A&P
    r'\bTHRIFTY\s+DRUG\b',  # Rite Aid subsidiary
    r'\bEDC\s+DRUG\b',  # EDC Drug chain
    r'\bCARR[\-\s]GOTTSTEIN\b',  # Carrs/Safeway Alaska
    r'\bSOUTHERN\s+FAMILY\s+MARKETS\b',  # BI-LO subsidiary
    r'\bHOMETOWN\s+PHARMACY\s+INC\b',  # Hometown chain (WI)
    r'\bPHARMACY\s+CORPORATION\s+OF\s+AMERICA\b',
    r'\bRIGHT\s+AID\b',  # Typo variant of Rite Aid
    r'\bDUANE\s+READE\b',
    r'\bBIG\s+B\s+DRUG\b',  # Big B Drug chain
    r'\bDRUG\s+EMPORIUM\b',  # Drug Emporium chain
    r'\bPHAR[\-\s]?MOR\b',  # Phar-Mor chain
    r'\bREVCO\b',  # Revco (CVS)
    r'\bPEOPLES?\s+DRUG\b',  # Peoples Drug (CVS)
    r'\bRIGHT\s+SOURCE\b',  # Humana mail order
]

# Non-independent pharmacy types to exclude (even if not a "chain")
NON_INDEPENDENT_PATTERNS = [
    # Hospital/health system pharmacies
    r'\bHOSPITAL\b', r'\bMEDICAL\s+CENTER\b', r'\bHEALTH\s+SYSTEM\b',
    r'\bHEALTH\s+SERVICES\b', r'\bHEALTH\s+NETWORK\b',
    r'\bMEDICAL\s+GROUP\b', r'\bHEALTHCARE\s+SYSTEM\b',
    r'\bMEDICAL\s+ASSOCIATES\b',

    # Government pharmacies
    r'\bVETERANS?\b', r'\bVA\s+', r'\bMILITARY\b', r'\bAIR\s+FORCE\b',
    r'\bARMY\b', r'\bNAVY\b', r'\bCOAST\s+GUARD\b',
    r'\bINDIAN\s+HEALTH\b', r'\bTRIBAL\b', r'\bNATION\s+HEALTH\b',
    r'\bCORRECTION', r'\bPRISON\b', r'\bDETENTION\b', r'\bJAIL\b',
    r'\bFEDERAL\b', r'\bSTATE\s+OF\b', r'\bCOUNTY\s+OF\b', r'\bCITY\s+OF\b',
    r'\bDEPARTMENT\s+OF\b',

    # University/academic pharmacies
    r'\bUNIVERSITY\b', r'\bCOLLEGE\s+OF\s+PHARMACY\b',
    r'\bSCHOOL\s+OF\s+PHARMACY\b', r'\bACADEMIC\b',

    # Non-retail pharmacy types
    r'\bINFUSION\b', r'\bHOME\s+HEALTH\b', r'\bHOME\s+CARE\b',
    r'\bLONG[\-\s]TERM\s+CARE\b', r'\bLTC\s+PHARMACY\b',
    r'\bNURSING\s+(HOME|FACILITY)\b', r'\bSKILLED\s+NURSING\b',
    r'\bASS?ISTED\s+LIVING\b', r'\bHOSPICE\b',
    r'\bCLOSED[\-\s]DOOR\b', r'\bNUCLEAR\s+PHARMACY\b',
    r'\bCLINICAL\s+TRIAL', r'\bRESEARCH\s+PHARMACY\b',
    r'\bMAIL[\-\s]ORDER\b', r'\bMAIL\s+SERVICE\b', r'\bCENTRAL\s+FILL\b',
    r'\bTELEPHARMACY\b',
]

# Compile patterns for performance
CHAIN_REGEX = [re.compile(p, re.IGNORECASE) for p in CHAIN_PATTERNS]
NON_INDEP_REGEX = [re.compile(p, re.IGNORECASE) for p in NON_INDEPENDENT_PATTERNS]


def is_chain_pharmacy(org_name):
    """Return True if the organization name matches a known chain pattern."""
    if not org_name or org_name.strip() == '<UNAVAIL>':
        return False
    for pattern in CHAIN_REGEX:
        if pattern.search(org_name):
            return True
    return False


def is_non_independent(org_name):
    """Return True if the organization name indicates a non-independent pharmacy type."""
    if not org_name or org_name.strip() == '<UNAVAIL>':
        return False
    for pattern in NON_INDEP_REGEX:
        if pattern.search(org_name):
            return True
    return False


def find_nppes_csv(extract_dir):
    """Find the main NPPES CSV file in the extracted directory."""
    patterns = [
        os.path.join(extract_dir, 'npidata_pfile_*.csv'),
        os.path.join(extract_dir, 'NPPES_Data_Dissemination_*', 'npidata_pfile_*.csv'),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            # Pick the largest file (skip _fileheader.csv variants)
            matches.sort(key=lambda f: os.path.getsize(f), reverse=True)
            return matches[0]
    # Try any large CSV
    for f in glob.glob(os.path.join(extract_dir, '**', '*.csv'), recursive=True):
        size = os.path.getsize(f)
        if size > 1_000_000_000:  # > 1GB = likely the main file
            return f
    return None


def process_nppes(zip_path, output_dir):
    """Extract and process NPPES data to identify independent pharmacies."""

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting NPPES processing...")
    print(f"  Source: {zip_path}")
    print(f"  Output: {output_dir}")

    extract_dir = os.path.join(output_dir, 'nppes_extracted')

    # Step 1: Extract ZIP
    if not os.path.exists(extract_dir):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Extracting ZIP file (~9GB when extracted)...")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # List contents
            for info in zf.infolist():
                print(f"  {info.filename} ({info.file_size / 1_000_000:.1f} MB)")
            zf.extractall(extract_dir)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Extraction complete.")
    else:
        print(f"  Using previously extracted files in {extract_dir}")

    # Step 2: Find the main CSV
    csv_path = find_nppes_csv(extract_dir)
    if not csv_path:
        print("ERROR: Could not find NPPES CSV file!")
        sys.exit(1)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing: {os.path.basename(csv_path)}")
    print(f"  File size: {os.path.getsize(csv_path) / 1_000_000_000:.2f} GB")

    # Step 3: Stream through the CSV, filtering for community/retail pharmacies
    # Key columns we need (by header name):
    # - NPI
    # - Entity Type Code (2 = Organization)
    # - Provider Organization Name (Legal Business Name)
    # - Provider Other Organization Name
    # - Provider First Line Business Practice Location Address
    # - Provider Second Line Business Practice Location Address
    # - Provider Business Practice Location Address City Name
    # - Provider Business Practice Location Address State Name
    # - Provider Business Practice Location Address Postal Code
    # - Provider Business Practice Location Address Telephone Number
    # - Healthcare Provider Taxonomy Code_1 (and _2 through _15)
    # - NPI Deactivation Reason Code (blank = active)

    chain_pharmacies = []
    non_independent_pharmacies = []
    independent_pharmacies = []

    total_rows = 0
    pharmacy_rows = 0

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_rows += 1

            if total_rows % 500000 == 0:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Processed {total_rows:,} rows... "
                      f"(found {pharmacy_rows:,} community pharmacies so far)")

            # Filter 1: Organizations only (Entity Type Code = 2)
            if row.get('Entity Type Code', '') != '2':
                continue

            # Filter 2: Active only (no deactivation reason)
            if row.get('NPI Deactivation Reason Code', '').strip():
                continue

            # Filter 3: Has community/retail pharmacy taxonomy
            is_community_pharmacy = False
            for i in range(1, 16):
                tax_col = f'Healthcare Provider Taxonomy Code_{i}'
                if row.get(tax_col, '') == '3336C0003X':
                    is_community_pharmacy = True
                    break

            if not is_community_pharmacy:
                continue

            pharmacy_rows += 1

            # Extract location address
            org_name = row.get('Provider Organization Name (Legal Business Name)', '').strip()
            other_name = row.get('Provider Other Organization Name', '').strip()
            # Use DBA name if available and not <UNAVAIL>, otherwise legal name
            if other_name and other_name != '<UNAVAIL>':
                display_name = other_name
            else:
                display_name = org_name
                other_name = ''  # Clean up <UNAVAIL>

            pharmacy = {
                'npi': row.get('NPI', '').strip(),
                'legal_name': org_name,
                'dba_name': other_name,
                'display_name': display_name,
                'address_1': row.get('Provider First Line Business Practice Location Address', '').strip(),
                'address_2': row.get('Provider Second Line Business Practice Location Address', '').strip(),
                'city': row.get('Provider Business Practice Location Address City Name', '').strip(),
                'state': row.get('Provider Business Practice Location Address State Name', '').strip(),
                'zip': row.get('Provider Business Practice Location Address Postal Code', '').strip()[:5],
                'phone': row.get('Provider Business Practice Location Address Telephone Number', '').strip(),
                'enumeration_date': row.get('Provider Enumeration Date', '').strip(),
                'last_updated': row.get('Last Update Date', '').strip(),
            }

            # Filter 4: US states only (exclude territories, military, etc.)
            valid_states = {
                'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
                'DC',
            }
            if pharmacy['state'] not in valid_states:
                continue

            # Filter 5: Chain pharmacies
            if is_chain_pharmacy(org_name) or is_chain_pharmacy(other_name):
                chain_pharmacies.append(pharmacy)
                continue

            # Filter 6: Non-independent types (hospitals, govt, specialty, etc.)
            if is_non_independent(org_name) or is_non_independent(other_name):
                non_independent_pharmacies.append(pharmacy)
                continue

            independent_pharmacies.append(pharmacy)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing complete!")
    print(f"  Total NPI records scanned: {total_rows:,}")
    print(f"  Community/Retail Pharmacies (US, active): {pharmacy_rows:,}")
    print(f"  Identified as chain: {len(chain_pharmacies):,}")
    print(f"  Identified as non-independent (hospital/govt/specialty/etc): {len(non_independent_pharmacies):,}")
    print(f"  Identified as independent: {len(independent_pharmacies):,}")

    # Step 4: Write output files

    # Independent pharmacies CSV
    indep_path = os.path.join(output_dir, 'independent_pharmacies_usa_feb2026.csv')
    fieldnames = ['npi', 'display_name', 'legal_name', 'dba_name',
                  'address_1', 'address_2', 'city', 'state', 'zip', 'phone',
                  'enumeration_date', 'last_updated']

    # Sort by state, then city, then name
    independent_pharmacies.sort(key=lambda x: (x['state'], x['city'], x['display_name']))

    with open(indep_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(independent_pharmacies)

    print(f"\n  Output: {indep_path}")
    print(f"  Records: {len(independent_pharmacies):,}")

    # State summary
    state_counts = {}
    for p in independent_pharmacies:
        st = p['state']
        state_counts[st] = state_counts.get(st, 0) + 1

    summary_path = os.path.join(output_dir, 'state_summary.csv')
    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['state', 'independent_count'])
        for st in sorted(state_counts.keys()):
            writer.writerow([st, state_counts[st]])

    print(f"\n  State Summary: {summary_path}")
    print("\n  Top 10 states by independent pharmacy count:")
    for st, count in sorted(state_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {st}: {count:,}")

    # Chain pharmacies (for reference/audit)
    chain_path = os.path.join(output_dir, 'chain_pharmacies_excluded.csv')
    chain_pharmacies.sort(key=lambda x: (x['state'], x['display_name']))
    with open(chain_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(chain_pharmacies)

    print(f"\n  Chain exclusions: {chain_path}")
    print(f"  Chain records: {len(chain_pharmacies):,}")

    # Non-independent pharmacies (for reference/audit)
    non_indep_path = os.path.join(output_dir, 'non_independent_excluded.csv')
    non_independent_pharmacies.sort(key=lambda x: (x['state'], x['display_name']))
    with open(non_indep_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(non_independent_pharmacies)

    print(f"\n  Non-independent exclusions: {non_indep_path}")
    print(f"  Non-independent records: {len(non_independent_pharmacies):,}")

    return indep_path, len(independent_pharmacies)


if __name__ == '__main__':
    base_dir = '/Users/matthewscott/Desktop/RetailMyMeds/Pharmacy_Database'
    zip_path = os.path.join(base_dir, 'nppes_feb2026.zip')

    if not os.path.exists(zip_path):
        print(f"ERROR: {zip_path} not found. Download it first.")
        sys.exit(1)

    process_nppes(zip_path, base_dir)
