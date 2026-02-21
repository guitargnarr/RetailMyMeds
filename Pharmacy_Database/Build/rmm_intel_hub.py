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

import csv
import hmac
import io
import os
import time
from functools import wraps
from pathlib import Path

import requests as http_client

from flask import (
    Flask, Response, jsonify, redirect, request, send_file, session, url_for,
)

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
app.secret_key = os.environ['SECRET_KEY']
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# In production (Render), set SESSION_COOKIE_SECURE=true via env
if os.environ.get('SESSION_COOKIE_SECURE', '').lower() == 'true':
    app.config['SESSION_COOKIE_SECURE'] = True

INTEL_USER = os.environ['INTEL_HUB_USER']
INTEL_PASS = os.environ['INTEL_HUB_PASS']

# Texume API for scorecard generation
TEXUME_API_URL = os.environ.get(
    'TEXUME_API_URL', 'https://texume-api.onrender.com',
)

# Brute-force protection: track failed attempts by IP
_failed_attempts: dict[str, list[float]] = {}
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutes

UI_PATH = Path(__file__).resolve().parent / 'rmm_intel_hub.html'


def login_required(f):
    """Redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RMM Intelligence Hub - Login</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #1A0A2E;
    color: #EEEAE4;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
  }
  .login-box {
    background: rgba(17, 7, 32, 0.85);
    border: 1px solid rgba(212, 168, 83, 0.3);
    border-radius: 6px;
    padding: 48px 40px;
    width: 360px;
    text-align: center;
  }
  .login-box h1 {
    font-size: 13px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: rgba(74, 111, 165, 0.7);
    margin-bottom: 12px;
  }
  .login-box h2 {
    font-size: 26px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 8px;
  }
  .login-box .subtitle {
    font-size: 13px;
    color: rgba(74, 111, 165, 0.6);
    margin-bottom: 32px;
  }
  .login-box .divider {
    width: 80px;
    height: 1px;
    background: #D4A853;
    margin: 0 auto 28px;
  }
  input {
    width: 100%;
    padding: 12px 16px;
    margin-bottom: 14px;
    background: rgba(26, 10, 46, 0.8);
    border: 1px solid rgba(212, 168, 83, 0.25);
    border-radius: 4px;
    color: #EEEAE4;
    font-size: 14px;
    outline: none;
  }
  input:focus { border-color: #D4A853; }
  input::placeholder { color: rgba(221, 216, 206, 0.35); }
  button {
    width: 100%;
    padding: 12px;
    background: rgba(212, 168, 83, 0.2);
    border: 1px solid rgba(212, 168, 83, 0.5);
    border-radius: 4px;
    color: #D4A853;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    margin-top: 6px;
  }
  button:hover { background: rgba(212, 168, 83, 0.3); }
  .error {
    color: #e87c7c;
    font-size: 13px;
    margin-bottom: 16px;
  }
</style>
</head>
<body>
<div class="login-box">
  <h1>RetailMyMeds</h1>
  <h2>Intelligence Hub</h2>
  <div class="divider"></div>
  <p class="subtitle">Authorized access only</p>
  <!-- ERROR_PLACEHOLDER -->
  <form method="POST">
    <input type="text" name="username" placeholder="Username" autocomplete="username" required>
    <input type="password" name="password" placeholder="Password"
      autocomplete="current-password" required>
    <button type="submit">Sign In</button>
  </form>
</div>
</body>
</html>"""


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


# --- Auth Routes ---


def _is_locked_out(ip: str) -> bool:
    """Check if an IP is locked out from too many failed attempts."""
    now = time.time()
    attempts = _failed_attempts.get(ip, [])
    # Prune old attempts
    attempts = [t for t in attempts if now - t < _LOCKOUT_SECONDS]
    _failed_attempts[ip] = attempts
    return len(attempts) >= _MAX_ATTEMPTS


def _record_failure(ip: str) -> None:
    """Record a failed login attempt."""
    _failed_attempts.setdefault(ip, []).append(time.time())


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if session.get('authenticated'):
        return redirect(url_for('index'))

    error = ''
    client_ip = request.remote_addr or '0.0.0.0'

    if request.method == 'POST':
        if _is_locked_out(client_ip):
            error = '<p class="error">Too many attempts. Try again in 5 minutes.</p>'
        else:
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            user_ok = hmac.compare_digest(username, INTEL_USER)
            pass_ok = hmac.compare_digest(password, INTEL_PASS)
            if user_ok and pass_ok:
                session.permanent = True
                session['authenticated'] = True
                session['login_time'] = time.time()
                # Clear failed attempts on success
                _failed_attempts.pop(client_ip, None)
                return redirect(url_for('index'))
            _record_failure(client_ip)
            error = '<p class="error">Invalid credentials</p>'

    return LOGIN_HTML.replace('<!-- ERROR_PLACEHOLDER -->', error)


@app.route('/logout')
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for('login'))


# --- Routes ---


@app.route('/')
@login_required
def index():
    """Serve the UI."""
    return send_file(UI_PATH)


@app.route('/api/search')
@login_required
def api_search():
    """Search pharmacies by NPI or name."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = search(q, limit=20)
    return jsonify([_pharmacy_summary(r) for r in results])


@app.route('/api/report/<npi>')
@login_required
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
@login_required
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


@app.route('/api/state/<state>/export')
@login_required
def api_state_export(state):
    """Export all matching pharmacies as downloadable CSV."""
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

    output = io.StringIO()
    fieldnames = [
        'npi', 'pharmacy_name', 'owner_name',
        'city', 'state', 'zip', 'phone',
        'grade', 'rmm_score', 'outreach_priority',
        'glp1_exposure_index', 'nearby_glp1_prescriber_claims',
        'est_monthly_glp1_fills', 'est_loss_per_fill',
        'est_annual_glp1_loss', 'hpsa_designated',
        'zip_diabetes_pct', 'zip_obesity_pct',
    ]
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction='ignore',
    )
    writer.writeheader()
    writer.writerows(sorted_rows)

    csv_bytes = output.getvalue().encode('utf-8')
    grade_suffix = f'_grade{grade}' if grade else ''
    filename = f'rmm_{st}{grade_suffix}.csv'

    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={
            'Content-Disposition': (
                f'attachment; filename="{filename}"'
            ),
        },
    )


@app.route('/api/states')
@login_required
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


# --- Scorecard Proxy (Intel Hub -> Texume API) ---


def _volume_dropdown(vol: float) -> str:
    """Map estimated Rx volume to ScorecardRequest dropdown."""
    if vol < 2000:
        return "Under 2,000"
    elif vol < 4000:
        return "2,000-3,999"
    elif vol < 6000:
        return "4,000-5,999"
    elif vol < 8000:
        return "6,000-7,999"
    return "8,000+"


def _glp1_dropdown(fills: float) -> str:
    """Map GLP-1 monthly fills to ScorecardRequest dropdown."""
    if fills < 100:
        return "Under 100"
    elif fills < 200:
        return "100-200"
    elif fills < 350:
        return "200-350"
    elif fills < 500:
        return "350-500"
    return "500+"


def _gov_payer_dropdown(pct: float) -> str:
    """Map gov payer % estimate to ScorecardRequest dropdown."""
    if pct < 20:
        return "Under 20%"
    elif pct < 40:
        return "20-40%"
    elif pct < 60:
        return "40-60%"
    elif pct < 80:
        return "60-80%"
    return "Over 80%"


def _build_scorecard_payload(pharmacy: dict) -> dict:
    """Map CSV pharmacy data to ScorecardRequest fields."""
    fills = _safe_float(
        pharmacy.get('est_monthly_glp1_fills', 0),
    )
    est_volume = fills / 0.07 if fills > 0 else 5000
    pct_65 = _safe_float(
        pharmacy.get('zip_pct_65_plus', 0),
    )
    gov_est = min(pct_65 * 2.5, 95)

    return {
        'pharmacy_name': pharmacy.get('pharmacy_name', ''),
        'owner_name': pharmacy.get('owner_name', ''),
        'city': pharmacy.get('city', ''),
        'state': pharmacy.get('state', ''),
        'monthly_rx_volume': _volume_dropdown(est_volume),
        'glp1_monthly_fills': _glp1_dropdown(fills),
        'gov_payer_pct': _gov_payer_dropdown(gov_est),
        'pms_system': 'Other',
        'num_technicians': '2',
        'aware_of_underwater_rx': "I'm not sure",
        'lost_patients_to_mail_order': 'No',
        'dir_fee_pressure': 'Significant squeeze',
        'dispenses_mfp_drugs': "I'm not sure",
    }


@app.route('/api/scorecard/<npi>', methods=['POST'])
@login_required
def api_scorecard(npi):
    """Generate a scorecard for a pharmacy via Texume API."""
    from pharmacy_lookup import lookup_npi
    pharmacy = lookup_npi(npi)
    if not pharmacy:
        return jsonify({'error': 'NPI not found'}), 404

    payload = _build_scorecard_payload(pharmacy)

    try:
        resp = http_client.post(
            f'{TEXUME_API_URL}/scorecard',
            json=payload,
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
        data.pop('pdf_base64', None)
        return jsonify(data)
    except http_client.exceptions.Timeout:
        return jsonify({
            'error': (
                'Scorecard generation timed out. '
                'The API may be warming up. '
                'Try again in 30 seconds.'
            ),
        }), 504
    except http_client.exceptions.ConnectionError:
        return jsonify({
            'error': (
                'Could not reach the scorecard service. '
                'It may be starting up.'
            ),
        }), 502
    except http_client.exceptions.HTTPError as e:
        return jsonify({
            'error': f'Scorecard service error: {e.response.status_code}',
        }), 502


@app.route('/api/scorecard/<npi>/pdf')
@login_required
def api_scorecard_pdf(npi):
    """Download scorecard PDF for a pharmacy."""
    from pharmacy_lookup import lookup_npi
    pharmacy = lookup_npi(npi)
    if not pharmacy:
        return jsonify({'error': 'NPI not found'}), 404

    payload = _build_scorecard_payload(pharmacy)
    name = pharmacy.get('pharmacy_name', 'pharmacy')
    slug = name.lower().replace(' ', '_')[:30]

    try:
        resp = http_client.post(
            f'{TEXUME_API_URL}/scorecard/pdf',
            json=payload,
            timeout=90,
        )
        resp.raise_for_status()
        return Response(
            resp.content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': (
                    f'attachment; filename="scorecard_{slug}.pdf"'
                ),
            },
        )
    except http_client.exceptions.Timeout:
        return jsonify({
            'error': 'PDF generation timed out. Try again.',
        }), 504
    except (
        http_client.exceptions.ConnectionError,
        http_client.exceptions.HTTPError,
    ):
        return jsonify({
            'error': 'Could not generate PDF. Try again.',
        }), 502


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
        'exposure_index': r.get(
            'glp1_exposure_index', '',
        ),
        'nearby_claims': r.get(
            'nearby_glp1_prescriber_claims', '',
        ),
        'monthly_fills': r.get(
            'est_monthly_glp1_fills', '',
        ),
        'loss_per_fill': r.get(
            'est_loss_per_fill', '',
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
        'exposure_index': r.get(
            'glp1_exposure_index', '',
        ),
        'nearby_claims': r.get(
            'nearby_glp1_prescriber_claims', '',
        ),
        'loss_per_fill': r.get(
            'est_loss_per_fill', '',
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

    # Exposure index
    exposure = pharmacy.get('glp1_exposure_index', '')
    nearby = pharmacy.get('nearby_glp1_prescriber_claims', '')
    if exposure:
        points.append({
            'label': 'Exposure',
            'text': (
                f"GLP-1 Exposure Index: {exposure}/100 "
                f"(nearby prescriber claims: {nearby})."
            ),
        })

    annual_loss = pharmacy.get('est_annual_glp1_loss', '')
    fills = pharmacy.get('est_monthly_glp1_fills', '')
    loss_per_fill = pharmacy.get('est_loss_per_fill', '')
    if annual_loss and annual_loss != 'N/A':
        try:
            loss_fmt = f"${int(float(annual_loss)):,}"
        except (ValueError, TypeError):
            loss_fmt = annual_loss
        try:
            lpf_fmt = f"${float(loss_per_fill):,.0f}"
        except (ValueError, TypeError):
            lpf_fmt = 'N/A'
        points.append({
            'label': 'GLP-1 Loss',
            'text': (
                f"Est. annual loss: {loss_fmt} "
                f"({fills} fills/mo x {lpf_fmt}/fill "
                f"NADAC-weighted, {state})."
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
