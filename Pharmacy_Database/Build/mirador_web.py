#!/usr/bin/env python3
"""
Mirador Web Interface
=====================
Flask server wrapping the Mirador chain pipeline with:
  - Pharmacy CSV lookup (search by NPI or name)
  - SSE-streamed chain execution via Ollama REST API
  - All runs logged to mirador_chain_log.txt

Usage:
  python3 mirador_web.py
  python3 mirador_web.py --port 5199

Opens http://localhost:5199 in the browser.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request, send_file

from mirador_chain import (
    CHAIN_PROMPT_TEMPLATE,
    DEFAULT_LOG,
    MODEL_1,
    MODEL_2,
    log_run,
)
from pharmacy_lookup import (
    build_enriched_question,
    lookup_npi,
    search,
)

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
        'model1': MODEL_1,
        'model2': MODEL_2,
        'log': str(DEFAULT_LOG),
    })


@app.route('/search')
def search_pharmacies():
    """Search pharmacies by NPI or name substring."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = search(q, limit=20)

    # Return lightweight summaries for the dropdown
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


def _stream_model(model: str, prompt: str):
    """Stream tokens from Ollama REST API. Yields strings."""
    resp = requests.post(
        OLLAMA_URL,
        json={'model': model, 'prompt': prompt, 'stream': True},
        stream=True,
        timeout=600,
    )
    resp.raise_for_status()

    full_output = []
    for line in resp.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        token = chunk.get('response', '')
        if token:
            full_output.append(token)
            yield token
        if chunk.get('done', False):
            break

    return ''.join(full_output)


@app.route('/run', methods=['POST'])
def run_chain():
    """Execute the Mirador chain with SSE streaming."""
    data = request.get_json(force=True)
    question = data.get('question', '').strip()
    npi = data.get('npi', '').strip()

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # Look up pharmacy if NPI provided
    pharmacy = lookup_npi(npi) if npi else None

    # Build enriched question with pharmacy data
    enriched = build_enriched_question(question, pharmacy)

    def generate():
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Stage 1: Model 1
        yield _sse('stage', 'model1')

        t0 = time.time()
        m1_tokens = []
        try:
            resp1 = requests.post(
                OLLAMA_URL,
                json={
                    'model': MODEL_1,
                    'prompt': enriched,
                    'stream': True,
                },
                stream=True,
                timeout=600,
            )
            resp1.raise_for_status()

            for line in resp1.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get('response', '')
                if token:
                    m1_tokens.append(token)
                    yield _sse('token', token)
                if chunk.get('done', False):
                    break
        except Exception as e:
            yield _sse('error', str(e))
            return

        m1_output = ''.join(m1_tokens)
        elapsed_m1 = time.time() - t0

        # Stage 2: Model 2
        yield _sse('stage', 'model2')

        m2_prompt = CHAIN_PROMPT_TEMPLATE.format(
            question=enriched,
            model1_output=m1_output,
        )

        t1 = time.time()
        m2_tokens = []
        try:
            resp2 = requests.post(
                OLLAMA_URL,
                json={
                    'model': MODEL_2,
                    'prompt': m2_prompt,
                    'stream': True,
                },
                stream=True,
                timeout=600,
            )
            resp2.raise_for_status()

            for line in resp2.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get('response', '')
                if token:
                    m2_tokens.append(token)
                    yield _sse('token', token)
                if chunk.get('done', False):
                    break
        except Exception as e:
            yield _sse('error', str(e))
            return

        m2_output = ''.join(m2_tokens)
        elapsed_m2 = time.time() - t1

        # Log the run
        log_run(
            DEFAULT_LOG, run_id, enriched,
            m1_output, m2_prompt, m2_output,
            elapsed_m1, elapsed_m2,
        )

        # Done
        yield _sse('done', json.dumps({
            'run_id': run_id,
            'elapsed_m1': round(elapsed_m1, 1),
            'elapsed_m2': round(elapsed_m2, 1),
            'total': round(elapsed_m1 + elapsed_m2, 1),
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
    # Escape newlines in data for SSE protocol
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
    print(f"  Model 1: {MODEL_1}")
    print(f"  Model 2: {MODEL_2}")
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
