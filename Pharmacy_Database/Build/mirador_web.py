#!/usr/bin/env python3
"""
Mirador Web Interface
=====================
Flask server wrapping the Mirador pipeline with:
  - Pharmacy CSV lookup (search by NPI or name)
  - SSE-streamed model output via Ollama REST API
  - Python fact validation (no LLM -- regex + CSV check)
  - All runs logged to mirador_chain_log.txt

Usage:
  python3 mirador_web.py
  python3 mirador_web.py --port 5199
"""

import json
import time
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request, send_file

from fact_validator import format_validation_json, validate_output
from mirador_chain import DEFAULT_LOG, MODEL, log_run
from pharmacy_lookup import build_enriched_question, lookup_npi, search

app = Flask(__name__)

OLLAMA_URL = 'http://localhost:11434/api/generate'
UI_PATH = Path(__file__).resolve().parent / 'mirador_ui.html'


# --- Routes ---


@app.route('/')
def index():
    """Serve the single-page UI."""
    return send_file(UI_PATH)


@app.route('/health')
def health():
    """Health check."""
    return jsonify({
        'status': 'ok',
        'model': MODEL,
        'log': str(DEFAULT_LOG),
    })


@app.route('/search')
def search_pharmacies():
    """Search pharmacies by NPI or name substring."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = search(q, limit=20)

    out = []
    for r in results:
        out.append({
            'npi': r.get('npi', ''),
            'name': r.get('pharmacy_name', ''),
            'city': r.get('city', ''),
            'state': r.get('state', ''),
            'zip': r.get('zip', ''),
            'grade': r.get('grade', ''),
            'score': r.get('rmm_score', ''),
            'hpsa': r.get('hpsa_designated', ''),
            'rucc': r.get('rucc_code', ''),
            'rural': r.get('rural_classification', ''),
            'priority': r.get('outreach_priority', ''),
            'monthly_fills': r.get(
                'est_monthly_glp1_fills', '',
            ),
            'annual_loss': r.get(
                'est_annual_glp1_loss', '',
            ),
        })
    return jsonify(out)


@app.route('/run', methods=['POST'])
def run_pipeline():
    """Execute model + fact validation with SSE streaming."""
    data = request.get_json(force=True)
    question = data.get('question', '').strip()
    npi = data.get('npi', '').strip()

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    pharmacy = lookup_npi(npi) if npi else None
    enriched = build_enriched_question(question, pharmacy)

    def generate():
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Stage 1: Model
        yield _sse('stage', 'model')

        t0 = time.time()
        tokens = []
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    'model': MODEL,
                    'prompt': enriched,
                    'stream': True,
                },
                stream=True,
                timeout=600,
            )
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get('response', '')
                if token:
                    tokens.append(token)
                    yield _sse('token', token)
                if chunk.get('done', False):
                    break
        except Exception as e:
            yield _sse('error', str(e))
            return

        model_output = ''.join(tokens)
        elapsed_model = time.time() - t0

        # Stage 2: Fact validation (Python, instant)
        yield _sse('stage', 'validation')

        t1 = time.time()
        result = validate_output(model_output, pharmacy)
        elapsed_val = time.time() - t1

        # Send validation as a single block
        val_json = format_validation_json(result)
        yield _sse('validation', json.dumps(val_json))

        # Log the run
        log_run(
            DEFAULT_LOG, run_id, enriched,
            model_output, result.summary,
            elapsed_model, elapsed_val,
        )

        # Done
        yield _sse('done', json.dumps({
            'run_id': run_id,
            'elapsed_model': round(elapsed_model, 1),
            'elapsed_validation': round(elapsed_val, 3),
            'total': round(elapsed_model + elapsed_val, 1),
            'pharmacy_npi': npi or None,
        }))

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


def _sse(event: str, data: str) -> str:
    """Format a Server-Sent Events message."""
    escaped = data.replace('\n', '\ndata: ')
    return f"event: {event}\ndata: {escaped}\n\n"


# --- Main ---

if __name__ == '__main__':
    import argparse
    import webbrowser

    parser = argparse.ArgumentParser(
        description='Mirador Web Interface',
    )
    parser.add_argument(
        '--port', type=int, default=5199,
        help='Port to run on (default: 5199)',
    )
    parser.add_argument(
        '--no-open', action='store_true',
        help='Do not open browser automatically',
    )
    args = parser.parse_args()

    url = f'http://localhost:{args.port}'
    print("Mirador Web Interface")
    print(f"  Model: {MODEL}")
    print(f"  Log: {DEFAULT_LOG}")
    print(f"  URL: {url}")

    if not args.no_open:
        webbrowser.open(url)

    app.run(
        host='127.0.0.1',
        port=args.port,
        debug=False,
        threaded=True,
    )
