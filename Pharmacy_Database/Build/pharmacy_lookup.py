#!/usr/bin/env python3
"""
RMM Pharmacy Lookup
====================
Loads the targeting CSV once and provides fast lookup by NPI, name,
or state. Also formats pharmacy data into structured context blocks
for injection into the Mirador chain.

Usage as module:
    from pharmacy_lookup import lookup_npi, search_name, search_state
    from pharmacy_lookup import build_enriched_question
"""

import csv
import re
from collections import defaultdict
from pathlib import Path


# --- CSV path ---

_CSV_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / 'Deliverables' / 'rmm_targeting_feb2026.csv'
)

# --- Dollar-formatted columns (strip to numeric at load) ---

_DOLLAR_COLS = {
    'est_annual_glp1_loss',
    'zip_median_income',
    'state_glp1_cost_per_pharmacy',
}

_DOLLAR_RE = re.compile(r'[\$,]')


def _strip_dollar(val: str) -> str:
    """Remove $ and commas so '$39,775' becomes '39775'."""
    if not val or val == 'N/A':
        return val
    return _DOLLAR_RE.sub('', val)


# --- Load and index ---

_by_npi: dict[str, dict] = {}
_by_state: dict[str, list[dict]] = defaultdict(list)
_all_rows: list[dict] = []


def _load() -> None:
    """Load CSV into in-memory indexes. Called once at import."""
    if _all_rows:
        return  # already loaded

    with open(_CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip dollar formatting for numeric columns
            for col in _DOLLAR_COLS:
                if col in row:
                    row[col] = _strip_dollar(row[col])

            npi = row.get('npi', '').strip()
            if npi:
                _by_npi[npi] = row

            state = row.get('state', '').strip().upper()
            if state:
                _by_state[state].append(row)

            _all_rows.append(row)


_load()


# --- Lookup functions ---


def lookup_npi(npi: str) -> dict | None:
    """Look up a pharmacy by NPI. Returns row dict or None."""
    return _by_npi.get(npi.strip())


def search_name(query: str, limit: int = 20) -> list[dict]:
    """Case-insensitive substring search on pharmacy_name."""
    q = query.strip().lower()
    if not q:
        return []
    results = []
    for row in _all_rows:
        name = row.get('pharmacy_name', '').lower()
        if q in name:
            results.append(row)
            if len(results) >= limit:
                break
    return results


def search_state(
    state: str, limit: int = 50,
) -> list[dict]:
    """Return pharmacies in a state (2-letter code)."""
    st = state.strip().upper()
    rows = _by_state.get(st, [])
    return rows[:limit]


# --- Context formatting ---


def format_pharmacy_context(row: dict) -> str:
    """Format a pharmacy row into a structured text block."""
    lines = [
        f"NPI: {row.get('npi', '')}",
        f"Name: {row.get('pharmacy_name', '')}",
        f"Owner: {row.get('owner_name', '')}",
        f"Location: {row.get('city', '')}, "
        f"{row.get('state', '')} {row.get('zip', '')}",
        f"Phone: {row.get('phone', '')}",
        '',
        f"Grade: {row.get('grade', '')} "
        f"({row.get('outreach_priority', '')})",
        f"RMM Score: {row.get('rmm_score', '')}",
        '',
        f"Est Monthly GLP-1 Fills: "
        f"{row.get('est_monthly_glp1_fills', '')}",
        f"Est Annual GLP-1 Loss: "
        f"${row.get('est_annual_glp1_loss', '')}",
        '',
        f"HPSA Designated: {row.get('hpsa_designated', '')}",
        f"HPSA Score: {row.get('hpsa_score', '')}",
        '',
        f"ZIP Diabetes %: {row.get('zip_diabetes_pct', '')}",
        f"ZIP Obesity %: {row.get('zip_obesity_pct', '')}",
        f"ZIP Age 65+ %: {row.get('zip_pct_65_plus', '')}",
        f"ZIP Median Income: "
        f"${row.get('zip_median_income', '')}",
        f"ZIP Population: {row.get('zip_population', '')}",
        '',
        f"State GLP-1 Cost/Pharmacy: "
        f"${row.get('state_glp1_cost_per_pharmacy', '')}",
        '',
        f"County: {row.get('county_name', '')} "
        f"(FIPS {row.get('county_fips', '')})",
        f"RUCC: {row.get('rucc_code', '')} "
        f"({row.get('rural_classification', '')})",
    ]
    return '\n'.join(lines)


def build_enriched_question(
    question: str,
    pharmacy: dict | None = None,
) -> str:
    """Wrap a question with pharmacy data context.

    If pharmacy is provided, prepends a structured data block
    so Model 1 has real per-pharmacy numbers to cite.
    """
    if pharmacy is None:
        return question

    ctx = format_pharmacy_context(pharmacy)
    return (
        f"=== PHARMACY DATA (from targeting database) ===\n"
        f"{ctx}\n"
        f"=== END PHARMACY DATA ===\n\n"
        f"{question}"
    )


# --- Convenience: search by query (NPI or name) ---


def search(query: str, limit: int = 20) -> list[dict]:
    """Search by NPI (exact) or name (substring)."""
    q = query.strip()
    if not q:
        return []

    # Try NPI first (all digits, 10 chars)
    if q.isdigit() and len(q) == 10:
        row = lookup_npi(q)
        if row:
            return [row]

    # Fall back to name search
    return search_name(q, limit=limit)


# --- CLI test ---

if __name__ == '__main__':
    import sys

    print(f"Loaded {len(_all_rows):,} pharmacies")
    print(f"NPI index: {len(_by_npi):,}")
    print(f"States: {len(_by_state)}")

    if len(sys.argv) > 1:
        q = ' '.join(sys.argv[1:])
        results = search(q)
        print(f"\nSearch '{q}': {len(results)} results")
        for r in results[:5]:
            print(
                f"  {r['npi']} | {r['pharmacy_name']} | "
                f"{r['city']}, {r['state']} | "
                f"Grade {r['grade']} ({r['rmm_score']})"
            )
        if results:
            print("\n--- Full context for first result ---")
            print(format_pharmacy_context(results[0]))
