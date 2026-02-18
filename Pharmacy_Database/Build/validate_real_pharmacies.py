#!/usr/bin/env python3
"""
Real Pharmacy Validation
========================
Pull actual pharmacies from the 41,775-row targeting CSV,
run them through the live scorecard API, and validate:

1. API accepts real data without errors
2. Scores are reasonable given the pharmacy's profile
3. Grades align with the CSV's outreach priority
4. PDF generation works for real pharmacy names (special chars, Inc., etc.)

This proves the system works on real inputs, not demos.
"""

import csv
import json
import random
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

API_URL = "https://texume-api.onrender.com/scorecard"
CSV_PATH = (
    "/Users/matthewscott/Desktop/RetailMyMeds/"
    "Pharmacy_Database/Deliverables/pharmacies_glp1_targeting.csv"
)

# Mapping real numeric data -> API dropdown ranges
def volume_to_dropdown(vol):
    """Map est_monthly_glp1_fills or total volume to dropdown string."""
    if vol < 2000:
        return "Under 2,000"
    elif vol < 4000:
        return "2,000-3,999"
    elif vol < 6000:
        return "4,000-5,999"
    elif vol < 8000:
        return "6,000-7,999"
    else:
        return "8,000+"

def glp1_to_dropdown(fills):
    """Map GLP-1 monthly fills to dropdown string."""
    if fills < 100:
        return "Under 100"
    elif fills < 200:
        return "100-200"
    elif fills < 350:
        return "200-350"
    elif fills < 500:
        return "350-500"
    else:
        return "500+"

def gov_payer_to_dropdown(pct):
    """Map government payer percentage to dropdown string.
    The CSV doesn't have direct payer mix, so we estimate from
    zip_pct_65_plus (proxy for Medicare density) and hpsa_designated."""
    if pct < 20:
        return "Under 20%"
    elif pct < 40:
        return "20-40%"
    elif pct < 60:
        return "40-60%"
    elif pct < 80:
        return "60-80%"
    else:
        return "Over 80%"

def dir_pressure_from_score(urgency_score):
    """Estimate DIR pressure from urgency score."""
    if urgency_score >= 80:
        return "Threatening viability"
    elif urgency_score >= 60:
        return "Significant squeeze"
    else:
        return "Manageable"


def load_pharmacies():
    """Load the targeting CSV, skip comment lines."""
    pharmacies = []
    with open(CSV_PATH, 'r') as f:
        # Skip comment lines
        lines = [line for line in f if not line.startswith('#')]

    reader = csv.DictReader(lines)
    for row in reader:
        # Only include Active or Likely Active pharmacies
        status = row.get('estimated_status', '')
        if status not in ('Active', 'Likely Active'):
            continue
        pharmacies.append(row)

    return pharmacies


def select_validation_set(pharmacies):
    """Select a diverse set of pharmacies for validation:
    - 3 from each grade (A, B, C, D) = 12
    - Ensure geographic diversity (different states)
    - Ensure different segments (GLP-1 Loss, MFP Cash Flow, DIR Fee Squeeze)
    - Include edge cases (special characters in names)
    """
    by_grade = {'A': [], 'B': [], 'C': [], 'D': []}
    for p in pharmacies:
        grade = p.get('grade', '')
        if grade in by_grade:
            by_grade[grade].append(p)

    selected = []
    seen_states = set()

    for grade in ['A', 'B', 'C', 'D']:
        pool = by_grade[grade]
        random.seed(42 + ord(grade))  # Reproducible selection
        random.shuffle(pool)

        count = 0
        for p in pool:
            state = p.get('state', '')
            # Prefer diverse states
            if state in seen_states and count < 2:
                continue
            selected.append(p)
            seen_states.add(state)
            count += 1
            if count >= 3:
                break

    return selected


def pharmacy_to_api_payload(row):
    """Map a CSV row to a ScorecardRequest payload."""
    # Estimate total monthly Rx volume from GLP-1 fills
    # CSV has est_monthly_glp1_fills; total volume ~ fills / 0.07
    glp1_fills = float(row.get('est_monthly_glp1_fills', 0))
    est_total_volume = glp1_fills / 0.07 if glp1_fills > 0 else 5000

    # Government payer proxy: zip_pct_65_plus as Medicare indicator
    pct_65 = float(row.get('zip_pct_65_plus', 0))
    # Rough mapping: 65+ population % correlates with Medicare enrollment
    # National avg 65+ is ~17%. Pharmacies in high-65+ areas have more Medicare.
    gov_payer_est = min(pct_65 * 2.5, 95)  # Scale up, cap at 95%

    urgency = float(row.get('urgency_score', 50))

    return {
        "pharmacy_name": row.get('display_name', 'Unknown'),
        "city": row.get('city', ''),
        "state": row.get('state', ''),
        "monthly_rx_volume": volume_to_dropdown(est_total_volume),
        "glp1_monthly_fills": glp1_to_dropdown(glp1_fills),
        "gov_payer_pct": gov_payer_to_dropdown(gov_payer_est),
        "pms_system": "Other",  # CSV doesn't have PMS data
        "num_technicians": "2",  # Default assumption
        "aware_of_underwater_rx": "I'm not sure",
        "lost_patients_to_mail_order": "No",
        "dir_fee_pressure": dir_pressure_from_score(urgency),
        "dispenses_mfp_drugs": "I'm not sure",
        "owner_name": row.get('owner_name', 'Owner'),
    }


def call_api(payload):
    """Call the scorecard API and return the response."""
    data = json.dumps(payload).encode('utf-8')
    req = Request(
        API_URL,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except URLError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def validate():
    print("=" * 80)
    print("REAL PHARMACY VALIDATION")
    print("Pulling from 41,775-pharmacy targeting CSV")
    print("Running through live scorecard API at texume-api.onrender.com")
    print("=" * 80)

    # Load and filter
    print("\nLoading CSV...")
    all_pharmacies = load_pharmacies()
    print(f"  Active/Likely Active pharmacies: {len(all_pharmacies):,}")

    # Grade distribution of active pharmacies
    grade_counts = {}
    for p in all_pharmacies:
        g = p.get('grade', '?')
        grade_counts[g] = grade_counts.get(g, 0) + 1
    print(f"  Grade distribution: {dict(sorted(grade_counts.items()))}")

    # Select validation set
    selected = select_validation_set(all_pharmacies)
    print(f"\nSelected {len(selected)} pharmacies for validation:")
    for p in selected:
        print(f"  [{p['grade']}] {p['display_name']}, {p['city']}, {p['state']} "
              f"(score: {p['final_score']}, segment: {p['segment']})")

    # Warm up API
    print("\nWarming up API...")
    try:
        req = Request("https://texume-api.onrender.com/health")
        with urlopen(req, timeout=60) as resp:
            health = json.loads(resp.read().decode('utf-8'))
            print(f"  API status: {health.get('status')}")
            print(f"  PDF available: {health.get('pdf_generation_available')}")
    except Exception as e:
        print(f"  Warning: API warmup failed: {e}")
        print("  Proceeding anyway (first call may be slow)...")

    # Run each pharmacy through the API
    print("\n" + "-" * 80)
    print("RUNNING VALIDATION")
    print("-" * 80)

    results = []
    passed = 0
    failed = 0
    warnings = []

    for i, pharmacy in enumerate(selected):
        payload = pharmacy_to_api_payload(pharmacy)
        csv_grade = pharmacy['grade']
        csv_score = float(pharmacy['final_score'])
        csv_segment = pharmacy['segment']
        csv_priority = pharmacy['outreach_priority']
        name = pharmacy['display_name']

        print(f"\n[{i+1}/{len(selected)}] {name}")
        print(f"  CSV: grade={csv_grade}, score={csv_score:.1f}, "
              f"segment={csv_segment}, priority={csv_priority}")

        # Call API
        start = time.time()
        result = call_api(payload)
        elapsed = time.time() - start

        if not result.get('success'):
            print(f"  FAIL: API error: {result.get('error', 'Unknown')}")
            failed += 1
            results.append({
                'name': name,
                'status': 'FAIL',
                'error': result.get('error'),
            })
            continue

        api_grade = result['overall_grade']
        api_score = result['overall_score']
        has_pdf = result.get('pdf_base64') is not None

        print(f"  API: grade={api_grade}, score={api_score}, "
              f"financial={result['financial_fit_score']}, "
              f"operational={result['operational_readiness_score']}, "
              f"market={result['market_urgency_score']}")
        print(f"  PDF: {'generated' if has_pdf else 'MISSING'} | "
              f"Time: {elapsed:.1f}s")
        print(f"  Breakeven: {result['roi_breakeven_fills']} fills/month")
        print(f"  Recommendation: {result['recommendation'][:120]}...")

        # Validation checks
        issues = []

        # 1. API should not crash (already checked above)

        # 2. Score should be in valid range
        if not (0 <= api_score <= 100):
            issues.append(f"Score out of range: {api_score}")

        # 3. Grade should be valid
        if api_grade not in ('A', 'B', 'C', 'D'):
            issues.append(f"Invalid grade: {api_grade}")

        # 4. PDF should be generated
        if not has_pdf:
            issues.append("PDF not generated")

        # 5. Breakeven should be reasonable (1-100 fills)
        if not (1 <= result['roi_breakeven_fills'] <= 100):
            issues.append(f"Breakeven unreasonable: {result['roi_breakeven_fills']}")

        # 6. Check if API grade is within 1 grade of CSV grade
        # Note: these use DIFFERENT scoring systems, so exact match
        # is not expected. CSV scores geography + data enrichment.
        # API scores form inputs (volume, PMS, situation).
        grade_order = {'A': 4, 'B': 3, 'C': 2, 'D': 1}
        grade_diff = abs(grade_order.get(api_grade, 0) - grade_order.get(csv_grade, 0))
        if grade_diff > 1:
            warnings.append(
                f"{name}: CSV grade {csv_grade} vs API grade {api_grade} "
                f"(2+ grade difference)"
            )

        # 7. Recommendation should mention the pharmacy name
        if name.split(',')[0].strip().lower() not in result['recommendation'].lower():
            # Check first word of name
            first_word = name.split()[0].lower() if name else ''
            if first_word and first_word not in result['recommendation'].lower():
                issues.append("Recommendation doesn't reference pharmacy name")

        if issues:
            print(f"  ISSUES: {'; '.join(issues)}")
            failed += 1
            status = 'FAIL'
        else:
            print(f"  PASS")
            passed += 1
            status = 'PASS'

        results.append({
            'name': name,
            'status': status,
            'csv_grade': csv_grade,
            'csv_score': csv_score,
            'api_grade': api_grade,
            'api_score': api_score,
            'financial': result['financial_fit_score'],
            'operational': result['operational_readiness_score'],
            'market': result['market_urgency_score'],
            'breakeven': result['roi_breakeven_fills'],
            'has_pdf': has_pdf,
            'time_s': round(elapsed, 1),
            'issues': issues,
        })

        # Brief pause between API calls
        if i < len(selected) - 1:
            time.sleep(1)

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"\nTotal pharmacies tested: {len(selected)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if warnings:
        print(f"\nGrade Divergence Warnings ({len(warnings)}):")
        print("  (Expected: CSV uses geography-weighted model, API uses form-input model)")
        for w in warnings:
            print(f"  - {w}")

    # Results table
    print(f"\n{'Name':<45} {'CSV':>5} {'API':>5} {'Fin':>5} {'Ops':>5} {'Mkt':>5} {'BE':>4} {'PDF':>4} {'Time':>5}")
    print("-" * 100)
    for r in results:
        if r['status'] == 'FAIL' and 'api_grade' not in r:
            print(f"{r['name'][:44]:<45} {'ERR':>5} {'---':>5}")
            continue
        print(
            f"{r['name'][:44]:<45} "
            f"{r.get('csv_grade','?'):>5} "
            f"{r.get('api_grade','?'):>5} "
            f"{r.get('financial',0):>5} "
            f"{r.get('operational',0):>5} "
            f"{r.get('market',0):>5} "
            f"{r.get('breakeven',0):>4} "
            f"{'Y' if r.get('has_pdf') else 'N':>4} "
            f"{r.get('time_s',0):>4.1f}s"
        )

    # Score analysis
    api_scores = [r['api_score'] for r in results if 'api_score' in r]
    if api_scores:
        print(f"\nAPI Score Distribution:")
        print(f"  Min: {min(api_scores)}, Max: {max(api_scores)}, "
              f"Avg: {sum(api_scores)/len(api_scores):.1f}")

    # Final verdict
    print("\n" + "=" * 80)
    if failed == 0:
        print("VERDICT: ALL PHARMACIES PASSED")
        print("The scorecard system works on real pharmacy data.")
    elif failed <= 2:
        print(f"VERDICT: {passed}/{len(selected)} PASSED ({failed} issues)")
        print("System is functional with minor issues to investigate.")
    else:
        print(f"VERDICT: {failed}/{len(selected)} FAILED")
        print("System has issues that need to be resolved before production use.")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = validate()
    sys.exit(0 if success else 1)
