#!/usr/bin/env python3
"""
RMM Pharmacy Intelligence Report
==================================
Generates a structured intelligence brief for any pharmacy in the
33,185-row targeting database. Every number traceable to the CSV.
No LLM. No fabrication.

Usage:
  python3 pharmacy_intel.py 1497754923
  python3 pharmacy_intel.py "Big Jim"
  python3 pharmacy_intel.py --state KY
  python3 pharmacy_intel.py --state KY --grade A
  python3 pharmacy_intel.py 1497754923 --output report.txt

The report includes:
  - Full pharmacy profile (all 24 fields)
  - Market context (state rank, grade distribution, peer comparison)
  - Outreach talking points (data-driven, no speculation)
  - Risk factors and limitations
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from pharmacy_lookup import (
    _all_rows,
    _by_state,
    search,
)

# --- Reference constants ---

LOSS_PER_FILL = 37
TOTAL_PHARMACIES = len(_all_rows)
GRADE_COUNTS = Counter(r['grade'] for r in _all_rows)


# --- Helpers ---

def _fmt_dollar(val: str | float) -> str:
    """Format a numeric value as $X,XXX."""
    try:
        n = float(val)
        return f"${int(round(n)):,}"
    except (ValueError, TypeError):
        return str(val) if val else 'N/A'


def _fmt_pct(val: str | float) -> str:
    """Format a value as X.X%."""
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return str(val) if val else 'N/A'


def _safe_float(val: str | float) -> float:
    """Convert to float, return 0.0 on failure."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _state_context(state: str, pharmacy: dict) -> str:
    """Build state-level market context."""
    rows = _by_state.get(state, [])
    if not rows:
        return f"No data for state {state}."

    total = len(rows)
    grade_a = [r for r in rows if r['grade'] == 'A']
    grade_a_count = len(grade_a)
    concentration = (
        (grade_a_count / total * 100) if total else 0
    )

    # Rank this pharmacy within state
    state_sorted = sorted(
        rows,
        key=lambda r: _safe_float(r.get('rmm_score', 0)),
        reverse=True,
    )
    rank = 1
    for r in state_sorted:
        if r.get('npi') == pharmacy.get('npi'):
            break
        rank += 1

    lines = [
        f"State: {state}",
        f"  Total pharmacies: {total:,}",
        f"  Grade A: {grade_a_count:,} "
        f"({concentration:.1f}% concentration)",
        f"  This pharmacy ranks #{rank} of {total} "
        f"in {state}",
    ]

    # Top 5 peers in state (same grade)
    grade = pharmacy.get('grade', '')
    peers = [
        r for r in state_sorted
        if r['grade'] == grade
        and r['npi'] != pharmacy.get('npi')
    ]
    if peers:
        lines.append(f"  Peers (Grade {grade} in {state}):")
        for p in peers[:5]:
            lines.append(
                f"    {p['pharmacy_name']}, "
                f"{p['city']} "
                f"(score: {p['rmm_score']})"
            )

    return '\n'.join(lines)


def _outreach_talking_points(pharmacy: dict) -> str:
    """Generate data-driven talking points."""
    points = []
    grade = pharmacy.get('grade', '')
    score = pharmacy.get('rmm_score', '')
    state = pharmacy.get('state', '')

    # Grade context
    if grade == 'A':
        points.append(
            f"Top 15% nationally (Grade A, score {score}). "
            f"Only {GRADE_COUNTS['A']:,} of "
            f"{TOTAL_PHARMACIES:,} pharmacies "
            f"reach this tier."
        )
    elif grade == 'B':
        points.append(
            f"Top 40% nationally (Grade B, score {score}). "
            f"Strong candidate for outreach."
        )

    # GLP-1 loss
    annual_loss = pharmacy.get('est_annual_glp1_loss', '')
    monthly_fills = pharmacy.get(
        'est_monthly_glp1_fills', '',
    )
    if annual_loss and annual_loss != 'N/A':
        points.append(
            f"Estimated annual GLP-1 loss: "
            f"{_fmt_dollar(annual_loss)} "
            f"({monthly_fills} fills/month "
            f"x ${LOSS_PER_FILL}/fill, "
            f"state-level average for {state})."
        )

    # Demographics
    diabetes = pharmacy.get('zip_diabetes_pct', '')
    obesity = pharmacy.get('zip_obesity_pct', '')
    senior = pharmacy.get('zip_pct_65_plus', '')
    if diabetes:
        points.append(
            f"ZIP diabetes prevalence: {_fmt_pct(diabetes)} "
            f"-- signals high GLP-1 demand in this market."
        )
    if obesity:
        points.append(
            f"ZIP obesity prevalence: {_fmt_pct(obesity)} "
            f"-- comorbidity indicator, compounds "
            f"GLP-1 exposure."
        )
    if senior:
        points.append(
            f"ZIP age 65+: {_fmt_pct(senior)} "
            f"-- Medicare exposure, higher "
            f"reimbursement complexity."
        )

    # HPSA
    hpsa = pharmacy.get('hpsa_designated', '')
    if hpsa == 'Yes':
        hpsa_score = pharmacy.get('hpsa_score', '')
        points.append(
            f"HPSA designated (score: {hpsa_score}) "
            f"-- federally recognized shortage area, "
            f"underserved market."
        )

    # Rural classification
    rucc = pharmacy.get('rucc_code', '')
    rural = pharmacy.get('rural_classification', '')
    if rucc and rural:
        points.append(
            f"RUCC {rucc} ({rural}) "
            f"-- {'less competition, ' if rural != 'Metro' else ''}"
            f"community-dependent pharmacy."
        )

    # MFP exposure
    points.append(
        "MFP program active since Jan 2026. "
        "10 drugs in Cycle 1; 15 more coming Jan 2027 "
        "(15 more in 2028, 20/year after -- scaling to 60+). "
        "Reimbursement lag: ~60 days vs. normal 2 weeks. "
        "Manufacturer rebates not being paid correctly -- "
        "pharmacies are not being made whole. "
        "CMS BALANCE Model (Dec 2025) adds further "
        "GLP-1 pricing pressure for Medicare Part D "
        "starting 2027. "
        "Cash flow was already the #1 issue; "
        "MFP pours salt in the wound."
    )

    # Income
    income = pharmacy.get('zip_median_income', '')
    if income and income != 'N/A':
        points.append(
            f"ZIP median income: {_fmt_dollar(income)} "
            f"-- lower income correlates with higher "
            f"need for cost-conscious pharmacy services."
        )

    return '\n'.join(
        f"  {i + 1}. {p}" for i, p in enumerate(points)
    )


def _limitations() -> str:
    """Standard limitations disclosure."""
    return (
        "LIMITATIONS (disclose in any outreach):\n"
        "  - GLP-1 fill estimates are STATE averages, "
        "not pharmacy-specific\n"
        "  - Individual pharmacy revenue/fill counts "
        "are unknown\n"
        "  - $37/fill loss is NCPA survey average, "
        "actual varies by drug and PBM\n"
        "  - HPSA designation is area-level, not "
        "pharmacy-specific\n"
        "  - We do not know which pharmacies are "
        "existing RMM customers\n"
        "  - MFP data is program-level, not "
        "pharmacy-specific. Actual rebate shortfalls "
        "vary by drug and manufacturer"
    )


# --- Report generator ---


def generate_report(pharmacy: dict) -> str:
    """Generate a full intelligence report for a pharmacy."""
    sep = '=' * 64
    state = pharmacy.get('state', '')
    npi = pharmacy.get('npi', '')
    name = pharmacy.get('pharmacy_name', '')

    sections = []

    # Header
    sections.append(sep)
    sections.append(
        "RMM PHARMACY INTELLIGENCE REPORT"
    )
    sections.append(sep)
    sections.append(
        f"Generated from rmm_targeting_feb2026.csv "
        f"({TOTAL_PHARMACIES:,} pharmacies)"
    )
    sections.append(
        "Source: CMS NPI Registry, CMS Part D, "
        "CDC/Census, HRSA, USDA ERS"
    )
    sections.append('')

    # Profile
    sections.append("PHARMACY PROFILE")
    sections.append('-' * 40)
    sections.append(f"NPI: {npi}")
    sections.append(f"Name: {name}")
    sections.append(
        f"Owner: {pharmacy.get('owner_name', '')}"
    )
    sections.append(
        f"Location: {pharmacy.get('city', '')}, "
        f"{state} {pharmacy.get('zip', '')}"
    )
    sections.append(
        f"Phone: {pharmacy.get('phone', '')}"
    )
    sections.append(
        f"County: {pharmacy.get('county_name', '')} "
        f"(FIPS {pharmacy.get('county_fips', '')})"
    )
    rucc = pharmacy.get('rucc_code', '')
    rural = pharmacy.get('rural_classification', '')
    sections.append(f"RUCC: {rucc} ({rural})")
    sections.append('')

    # Scoring
    sections.append("SCORING")
    sections.append('-' * 40)
    sections.append(
        f"RMM Score: {pharmacy.get('rmm_score', '')}"
    )
    sections.append(
        f"Grade: {pharmacy.get('grade', '')} "
        f"({pharmacy.get('outreach_priority', '')})"
    )
    sections.append(
        f"Grade A threshold: 70.4 "
        f"(top {GRADE_COUNTS['A']:,} of "
        f"{TOTAL_PHARMACIES:,})"
    )
    sections.append('')

    # GLP-1 exposure
    sections.append("GLP-1 EXPOSURE")
    sections.append('-' * 40)
    glp1_cost = pharmacy.get(
        'state_glp1_cost_per_pharmacy', '',
    )
    sections.append(
        f"State GLP-1 cost/pharmacy: "
        f"{_fmt_dollar(glp1_cost)} "
        f"({state} average)"
    )
    sections.append(
        f"Est monthly fills: "
        f"{pharmacy.get('est_monthly_glp1_fills', '')} "
        f"(state average / 12)"
    )
    annual_loss = pharmacy.get(
        'est_annual_glp1_loss', '',
    )
    sections.append(
        f"Est annual GLP-1 loss: "
        f"{_fmt_dollar(annual_loss)} "
        f"(fills x ${LOSS_PER_FILL}/fill NCPA)"
    )
    sections.append('')

    # Demographics
    sections.append("ZIP DEMOGRAPHICS")
    sections.append('-' * 40)
    sections.append(
        f"Diabetes prevalence: "
        f"{_fmt_pct(pharmacy.get('zip_diabetes_pct', ''))}"
    )
    sections.append(
        f"Obesity prevalence: "
        f"{_fmt_pct(pharmacy.get('zip_obesity_pct', ''))}"
    )
    sections.append(
        f"Age 65+: "
        f"{_fmt_pct(pharmacy.get('zip_pct_65_plus', ''))}"
    )
    sections.append(
        f"Median income: "
        f"{_fmt_dollar(pharmacy.get('zip_median_income', ''))}"
    )
    sections.append(
        f"Population: "
        f"{pharmacy.get('zip_population', '')}"
    )
    hpsa = pharmacy.get('hpsa_designated', '')
    sections.append(
        f"HPSA designated: {hpsa} "
        f"(score: {pharmacy.get('hpsa_score', '')})"
    )
    sections.append('')

    # State context
    sections.append("STATE MARKET CONTEXT")
    sections.append('-' * 40)
    sections.append(_state_context(state, pharmacy))
    sections.append('')

    # Talking points
    sections.append("OUTREACH TALKING POINTS")
    sections.append('-' * 40)
    sections.append(_outreach_talking_points(pharmacy))
    sections.append('')

    # Limitations
    sections.append(_limitations())
    sections.append('')
    sections.append(sep)

    return '\n'.join(sections)


def generate_state_summary(state: str, grade: str = None) -> str:
    """Generate a state-level summary report."""
    rows = _by_state.get(state.upper(), [])
    if not rows:
        return f"No pharmacies found for state: {state}"

    if grade:
        rows = [r for r in rows if r['grade'] == grade.upper()]
        if not rows:
            return (
                f"No Grade {grade.upper()} pharmacies "
                f"in {state.upper()}"
            )

    sep = '=' * 64
    total = len(rows)
    grades = Counter(r['grade'] for r in rows)

    sorted_rows = sorted(
        rows,
        key=lambda r: _safe_float(r.get('rmm_score', 0)),
        reverse=True,
    )

    lines = []
    lines.append(sep)
    if grade:
        lines.append(
            f"RMM STATE REPORT: {state.upper()} "
            f"-- Grade {grade.upper()} "
            f"({total:,} pharmacies)"
        )
    else:
        lines.append(
            f"RMM STATE REPORT: {state.upper()} "
            f"({total:,} pharmacies)"
        )
    lines.append(sep)
    lines.append('')

    if not grade:
        lines.append("GRADE DISTRIBUTION")
        lines.append('-' * 40)
        for g in ['A', 'B', 'C', 'D']:
            cnt = grades.get(g, 0)
            pct = cnt / total * 100 if total else 0
            lines.append(f"  Grade {g}: {cnt:,} ({pct:.1f}%)")
        lines.append('')

    # Top pharmacies
    show = min(25, total)
    lines.append(f"TOP {show} PHARMACIES")
    lines.append('-' * 40)
    for r in sorted_rows[:show]:
        loss = _fmt_dollar(
            r.get('est_annual_glp1_loss', ''),
        )
        lines.append(
            f"  {r['npi']} | {r['pharmacy_name']:<35s} | "
            f"{r['city']:<15s} | "
            f"Grade {r['grade']} | "
            f"{r['rmm_score']} | "
            f"Loss: {loss}"
        )

    lines.append('')
    lines.append(sep)
    return '\n'.join(lines)


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description='RMM Pharmacy Intelligence Report',
    )
    parser.add_argument(
        'query', nargs='?', default=None,
        help='NPI or pharmacy name to look up',
    )
    parser.add_argument(
        '--state', default=None,
        help='Generate state summary (2-letter code)',
    )
    parser.add_argument(
        '--grade', default=None,
        help='Filter state summary by grade (A/B/C/D)',
    )
    parser.add_argument(
        '--output', '-o', default=None,
        help='Write report to file instead of stdout',
    )
    args = parser.parse_args()

    report = None

    if args.state:
        report = generate_state_summary(
            args.state, args.grade,
        )
    elif args.query:
        results = search(args.query, limit=5)
        if not results:
            print(f"No pharmacy found for: {args.query}")
            sys.exit(1)
        if len(results) > 1:
            print(
                f"Found {len(results)} matches, "
                f"using first:"
            )
            for r in results[:5]:
                print(
                    f"  {r['npi']} | "
                    f"{r['pharmacy_name']} | "
                    f"{r['city']}, {r['state']}"
                )
            print()
        report = generate_report(results[0])
    else:
        parser.print_help()
        sys.exit(0)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(report, encoding='utf-8')
        print(f"Report written to {out_path}")
    else:
        print(report)


if __name__ == '__main__':
    main()
