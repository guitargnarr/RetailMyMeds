#!/usr/bin/env python3
"""
RMM Intelligence Hub
=====================
Web interface for pharmacy intelligence reports.
No Ollama dependency. Every number from the CSV.

Usage:
  python3 rmm_intel_hub.py
  python3 rmm_intel_hub.py --port 5199

Kevin and Arica open http://localhost:5199 and use it.
"""

from pathlib import Path

from flask import Flask, jsonify, request, send_file

from pharmacy_intel import (
    GRADE_COUNTS,
    TOTAL_PHARMACIES,
    generate_report,
    generate_state_summary,
)
from pharmacy_lookup import (
    _by_state,
    search,
)

app = Flask(__name__)

UI_PATH = Path(__file__).resolve().parent / 'rmm_intel_hub.html'


# --- Precompute state summary data ---

_STATE_SUMMARY: dict[str, dict] = {}


def _build_state_summaries() -> None:
    """Build state summary stats at startup."""
    from collections import Counter
    for st, rows in _by_state.items():
        total = len(rows)
        grades = Counter(r['grade'] for r in rows)
        _STATE_SUMMARY[st] = {
            'state': st,
            'total': total,
            'grade_a': grades.get('A', 0),
            'grade_b': grades.get('B', 0),
            'grade_c': grades.get('C', 0),
            'grade_d': grades.get('D', 0),
        }


_build_state_summaries()


# --- Routes ---


@app.route('/')
def index():
    """Serve the UI."""
    return send_file(UI_PATH)


@app.route('/api/search')
def api_search():
    """Search pharmacies by NPI or name."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = search(q, limit=20)
    return jsonify([_pharmacy_summary(r) for r in results])


@app.route('/api/report/<npi>')
def api_report(npi):
    """Generate full intel report for a pharmacy."""
    from pharmacy_lookup import lookup_npi
    pharmacy = lookup_npi(npi)
    if not pharmacy:
        return jsonify({'error': 'NPI not found'}), 404

    # Return both structured data and formatted text
    return jsonify({
        'pharmacy': _pharmacy_detail(pharmacy),
        'state_context': _state_context(pharmacy),
        'talking_points': _talking_points(pharmacy),
        'report_text': generate_report(pharmacy),
    })


@app.route('/api/state/<state>')
def api_state(state):
    """State summary with optional grade filter."""
    grade = request.args.get('grade', '').upper() or None
    st = state.upper()

    if st not in _by_state:
        return jsonify({'error': f'State {st} not found'}), 404

    rows = _by_state[st]
    if grade:
        rows = [r for r in rows if r['grade'] == grade]

    sorted_rows = sorted(
        rows,
        key=lambda r: _safe_float(r.get('rmm_score', 0)),
        reverse=True,
    )

    return jsonify({
        'state': st,
        'grade_filter': grade,
        'total': len(rows),
        'summary': _STATE_SUMMARY.get(st, {}),
        'pharmacies': [
            _pharmacy_summary(r) for r in sorted_rows[:50]
        ],
        'report_text': generate_state_summary(st, grade),
    })


@app.route('/api/states')
def api_states():
    """Return all state summaries for the overview."""
    states = sorted(
        _STATE_SUMMARY.values(),
        key=lambda s: s['grade_a'],
        reverse=True,
    )
    return jsonify({
        'total_pharmacies': TOTAL_PHARMACIES,
        'grade_counts': dict(GRADE_COUNTS),
        'states': states,
    })


@app.route('/api/health')
def api_health():
    """Health check."""
    return jsonify({
        'status': 'ok',
        'pharmacies': TOTAL_PHARMACIES,
        'states': len(_STATE_SUMMARY),
    })


# --- Formatters ---


def _safe_float(val) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _pharmacy_summary(r: dict) -> dict:
    """Lightweight pharmacy summary for search results."""
    return {
        'npi': r.get('npi', ''),
        'name': r.get('pharmacy_name', ''),
        'owner': r.get('owner_name', ''),
        'city': r.get('city', ''),
        'state': r.get('state', ''),
        'zip': r.get('zip', ''),
        'phone': r.get('phone', ''),
        'grade': r.get('grade', ''),
        'score': r.get('rmm_score', ''),
        'priority': r.get('outreach_priority', ''),
        'hpsa': r.get('hpsa_designated', ''),
        'rucc': r.get('rucc_code', ''),
        'rural': r.get('rural_classification', ''),
        'monthly_fills': r.get(
            'est_monthly_glp1_fills', '',
        ),
        'annual_loss': r.get(
            'est_annual_glp1_loss', '',
        ),
    }


def _pharmacy_detail(r: dict) -> dict:
    """Full pharmacy detail for report view."""
    return {
        **_pharmacy_summary(r),
        'hpsa_score': r.get('hpsa_score', ''),
        'diabetes_pct': r.get('zip_diabetes_pct', ''),
        'obesity_pct': r.get('zip_obesity_pct', ''),
        'pct_65_plus': r.get('zip_pct_65_plus', ''),
        'median_income': r.get('zip_median_income', ''),
        'population': r.get('zip_population', ''),
        'glp1_cost': r.get(
            'state_glp1_cost_per_pharmacy', '',
        ),
        'county_fips': r.get('county_fips', ''),
        'county_name': r.get('county_name', ''),
    }


def _state_context(pharmacy: dict) -> dict:
    """State context for a pharmacy."""
    state = pharmacy.get('state', '')
    rows = _by_state.get(state, [])
    total = len(rows)
    grade_a = sum(1 for r in rows if r['grade'] == 'A')

    # Rank within state
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

    # Peers (same grade)
    grade = pharmacy.get('grade', '')
    peers = [
        _pharmacy_summary(r)
        for r in state_sorted
        if r['grade'] == grade
        and r['npi'] != pharmacy.get('npi')
    ][:5]

    return {
        'state': state,
        'total': total,
        'grade_a': grade_a,
        'concentration': (
            round(grade_a / total * 100, 1)
            if total else 0
        ),
        'rank': rank,
        'peers': peers,
    }


def _talking_points(pharmacy: dict) -> list[dict]:
    """Structured talking points."""
    points = []
    grade = pharmacy.get('grade', '')
    score = pharmacy.get('rmm_score', '')
    state = pharmacy.get('state', '')

    if grade == 'A':
        points.append({
            'label': 'National Ranking',
            'text': (
                f"Top 15% nationally (Grade A, "
                f"score {score}). Only "
                f"{GRADE_COUNTS['A']:,} of "
                f"{TOTAL_PHARMACIES:,} qualify."
            ),
        })
    elif grade == 'B':
        points.append({
            'label': 'National Ranking',
            'text': (
                f"Top 40% nationally (Grade B, "
                f"score {score})."
            ),
        })

    annual_loss = pharmacy.get('est_annual_glp1_loss', '')
    fills = pharmacy.get('est_monthly_glp1_fills', '')
    if annual_loss and annual_loss != 'N/A':
        try:
            loss_fmt = f"${int(float(annual_loss)):,}"
        except (ValueError, TypeError):
            loss_fmt = annual_loss
        points.append({
            'label': 'GLP-1 Loss',
            'text': (
                f"Est. annual loss: {loss_fmt} "
                f"({fills} fills/mo x $37/fill, "
                f"{state} state average)."
            ),
        })

    diabetes = pharmacy.get('zip_diabetes_pct', '')
    if diabetes:
        points.append({
            'label': 'Diabetes',
            'text': (
                f"ZIP diabetes: {diabetes}% "
                f"-- high GLP-1 demand signal."
            ),
        })

    obesity = pharmacy.get('zip_obesity_pct', '')
    if obesity:
        points.append({
            'label': 'Obesity',
            'text': (
                f"ZIP obesity: {obesity}% "
                f"-- comorbidity compounds "
                f"GLP-1 exposure."
            ),
        })

    senior = pharmacy.get('zip_pct_65_plus', '')
    if senior:
        points.append({
            'label': 'Seniors',
            'text': (
                f"ZIP age 65+: {senior}% "
                f"-- Medicare reimbursement "
                f"complexity."
            ),
        })

    hpsa = pharmacy.get('hpsa_designated', '')
    if hpsa == 'Yes':
        points.append({
            'label': 'HPSA',
            'text': (
                f"Federally designated shortage area "
                f"(score: "
                f"{pharmacy.get('hpsa_score', '')})."
            ),
        })

    rucc = pharmacy.get('rucc_code', '')
    rural = pharmacy.get('rural_classification', '')
    if rucc and rural:
        points.append({
            'label': 'Rural',
            'text': f"RUCC {rucc} ({rural}).",
        })

    return points


# --- Main ---

if __name__ == '__main__':
    import argparse
    import webbrowser

    parser = argparse.ArgumentParser(
        description='RMM Intelligence Hub',
    )
    parser.add_argument(
        '--port', type=int, default=5199,
    )
    parser.add_argument(
        '--no-open', action='store_true',
    )
    args = parser.parse_args()

    url = f'http://localhost:{args.port}'
    print("RMM Intelligence Hub")
    print(f"  Pharmacies: {TOTAL_PHARMACIES:,}")
    print(f"  States: {len(_STATE_SUMMARY)}")
    print(f"  URL: {url}")

    if not args.no_open:
        webbrowser.open(url)

    app.run(
        host='127.0.0.1',
        port=args.port,
        debug=False,
        threaded=True,
    )
