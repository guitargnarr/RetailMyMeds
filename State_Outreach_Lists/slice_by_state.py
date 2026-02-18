#!/usr/bin/env python3
"""
State-Sliced Outreach Lists
============================
Slices the 41,775-row targeting CSV into per-state outreach-ready CSVs.

- Top 10 states by active pharmacy count + opportunity score
- Simplified columns for outbound workflow (Arica's use case)
- Each file sorted by outreach_priority then final_score descending
- Summary stats per state printed to stdout

Output: ~/Desktop/RetailMyMeds/State_Outreach_Lists/<STATE>_outreach.csv
"""

import csv
import os
from collections import defaultdict
from pathlib import Path

CSV_PATH = (
    "/Users/matthewscott/Desktop/RetailMyMeds/"
    "Pharmacy_Database/Deliverables/pharmacies_glp1_targeting.csv"
)
OUTPUT_DIR = Path(__file__).parent

# Columns Arica needs for outbound (simplified from 36 to 12)
OUTREACH_COLUMNS = [
    'display_name',
    'owner_name',
    'city',
    'state',
    'zip',
    'phone',
    'grade',
    'outreach_priority',
    'segment',
    'est_monthly_glp1_fills',
    'est_annual_loss',
    'final_score',
]

PRIORITY_ORDER = {
    'Immediate Outreach': 0,
    'Nurture': 1,
    'Conditional': 2,
    'Deprioritize': 3,
}


def load_active_pharmacies():
    """Load CSV, skip comments, filter to Active/Likely Active only."""
    pharmacies = []
    with open(CSV_PATH, 'r') as f:
        lines = [line for line in f if not line.startswith('#')]

    reader = csv.DictReader(lines)
    for row in reader:
        status = row.get('estimated_status', '')
        if status in ('Active', 'Likely Active'):
            pharmacies.append(row)
    return pharmacies


def rank_states(pharmacies):
    """Rank states by composite: count * avg_opportunity_score."""
    by_state = defaultdict(list)
    for p in pharmacies:
        by_state[p['state']].append(p)

    state_scores = []
    for state, pharms in by_state.items():
        count = len(pharms)
        avg_score = sum(float(p['final_score']) for p in pharms) / count
        immediate = sum(1 for p in pharms if p['outreach_priority'] == 'Immediate Outreach')
        state_scores.append({
            'state': state,
            'count': count,
            'avg_score': round(avg_score, 1),
            'immediate': immediate,
            'composite': round(count * avg_score / 100, 1),
        })

    return sorted(state_scores, key=lambda s: s['composite'], reverse=True)


def write_state_csv(state, pharmacies):
    """Write a single state's outreach CSV."""
    # Sort: priority order first, then score descending
    sorted_pharms = sorted(
        pharmacies,
        key=lambda p: (
            PRIORITY_ORDER.get(p['outreach_priority'], 99),
            -float(p['final_score']),
        )
    )

    output_path = OUTPUT_DIR / f"{state}_outreach.csv"
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTREACH_COLUMNS)
        writer.writeheader()
        for p in sorted_pharms:
            row = {col: p.get(col, '') for col in OUTREACH_COLUMNS}
            writer.writerow(row)

    return output_path, len(sorted_pharms)


def main():
    print("=" * 70)
    print("STATE-SLICED OUTREACH LISTS")
    print("=" * 70)

    print("\nLoading active pharmacies...")
    pharmacies = load_active_pharmacies()
    print(f"  Total active: {len(pharmacies):,}")

    print("\nRanking states...")
    rankings = rank_states(pharmacies)

    # Print full ranking table
    print(f"\n{'Rank':>4} {'State':>6} {'Active':>7} {'Avg Score':>10} "
          f"{'Immediate':>10} {'Composite':>10}")
    print("-" * 55)
    for i, s in enumerate(rankings[:20], 1):
        print(f"{i:>4} {s['state']:>6} {s['count']:>7,} {s['avg_score']:>10.1f} "
              f"{s['immediate']:>10,} {s['composite']:>10.1f}")

    # Slice top 10
    top_10 = rankings[:10]
    by_state = defaultdict(list)
    for p in pharmacies:
        by_state[p['state']].append(p)

    print(f"\nGenerating outreach CSVs for top 10 states...")
    print(f"Output: {OUTPUT_DIR}/\n")

    total_written = 0
    for s in top_10:
        state = s['state']
        path, count = write_state_csv(state, by_state[state])
        total_written += count
        print(f"  {state}: {count:>5,} pharmacies -> {path.name}")

    # Also generate an "ALL_IMMEDIATE" CSV across all states
    immediate = [p for p in pharmacies if p['outreach_priority'] == 'Immediate Outreach']
    immediate_sorted = sorted(immediate, key=lambda p: -float(p['final_score']))

    all_path = OUTPUT_DIR / "ALL_IMMEDIATE_outreach.csv"
    with open(all_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTREACH_COLUMNS)
        writer.writeheader()
        for p in immediate_sorted:
            row = {col: p.get(col, '') for col in OUTREACH_COLUMNS}
            writer.writerow(row)

    print(f"\n  ALL: {len(immediate):>5,} Immediate Outreach pharmacies -> ALL_IMMEDIATE_outreach.csv")

    print(f"\n{'=' * 70}")
    print(f"DONE: {total_written:,} pharmacies across {len(top_10)} state files")
    print(f"      {len(immediate):,} Immediate Outreach pharmacies in ALL_IMMEDIATE_outreach.csv")
    print(f"      12 columns per row (simplified for outbound workflow)")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
