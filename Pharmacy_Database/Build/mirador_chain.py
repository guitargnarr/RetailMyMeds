#!/usr/bin/env python3
"""
Mirador Pipeline
=================
Single model (rmm-pharmacy-expert) + Python fact validation.

The model produces analysis grounded in real pharmacy data
(when enriched via pharmacy_lookup). The fact validator then
extracts every number, dollar amount, and percentage from the
output and checks each against the CSV and reference constants.

Usage:
  python3 mirador_chain.py "Your question here"
  python3 mirador_chain.py --interactive
  python3 mirador_chain.py --npi 1497754923 "Question about this pharmacy"

The log file captures every run with timestamps, model output,
and fact validation results.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# --- Configuration ---

MODEL = 'rmm-pharmacy-expert'
DEFAULT_LOG = Path(__file__).resolve().parent / 'mirador_chain_log.txt'


# --- Ollama Runner ---

def run_model(model: str, prompt: str, timeout: int = 300) -> str:
    """Run an Ollama model and return full output."""
    proc = subprocess.run(
        ['ollama', 'run', model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        err = proc.stderr.strip()
        raise RuntimeError(f"{model} failed: {err}")
    return proc.stdout.strip()


# --- Logger ---

def log_run(
    log_path: Path,
    run_id: str,
    question: str,
    model_output: str,
    validation_summary: str,
    elapsed_model: float,
    elapsed_validation: float,
) -> None:
    """Append a run to the log file."""
    sep = '=' * 72
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n{sep}\n")
        f.write(f"MIRADOR RUN: {run_id}\n")
        f.write(
            f"Timestamp: {datetime.now().isoformat()}\n"
        )
        f.write(f"Model: {MODEL}\n")
        f.write(f"Model elapsed: {elapsed_model:.1f}s\n")
        f.write(
            f"Validation elapsed: "
            f"{elapsed_validation:.1f}s\n"
        )
        total = elapsed_model + elapsed_validation
        f.write(f"Total elapsed: {total:.1f}s\n")
        f.write(f"{sep}\n\n")

        f.write("--- QUESTION ---\n")
        f.write(f"{question}\n\n")

        f.write(f"--- MODEL OUTPUT ({MODEL}) ---\n")
        f.write(f"{model_output}\n\n")

        f.write("--- FACT VALIDATION ---\n")
        f.write(f"{validation_summary}\n\n")

        f.write(f"{sep}\n")
        f.write("END OF RUN\n")
        f.write(f"{sep}\n\n")


# --- Pipeline Execution ---

def run_pipeline(
    question: str,
    log_path: Path,
    pharmacy: dict | None = None,
    verbose: bool = True,
) -> tuple[str, str]:
    """Execute model + fact validation.

    Returns (model_output, validation_summary).
    """
    from fact_validator import validate_output
    from pharmacy_lookup import build_enriched_question

    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    enriched = build_enriched_question(question, pharmacy)

    if verbose:
        print(f"[Mirador] Run {run_id}")
        print(f"[Mirador] Question: {question[:80]}...")
        if pharmacy:
            npi = pharmacy.get('npi', '?')
            name = pharmacy.get('pharmacy_name', '?')
            print(f"[Mirador] Pharmacy: {npi} ({name})")
        print(f"[Mirador] Model: {MODEL}...")

    t0 = datetime.now()
    model_output = run_model(MODEL, enriched, timeout=300)
    t1 = datetime.now()
    elapsed_model = (t1 - t0).total_seconds()

    if verbose:
        print(
            f"[Mirador] Model complete ({elapsed_model:.1f}s)"
        )
        print("[Mirador] Fact validation...")

    t2 = datetime.now()
    result = validate_output(model_output, pharmacy)
    t3 = datetime.now()
    elapsed_val = (t3 - t2).total_seconds()

    if verbose:
        print(
            f"[Mirador] Validation: {result.verified}/"
            f"{len(result.claims)} verified, "
            f"{result.flagged} flagged"
        )
        total = elapsed_model + elapsed_val
        print(f"[Mirador] Total: {total:.1f}s")

    log_run(
        log_path, run_id, enriched,
        model_output, result.summary,
        elapsed_model, elapsed_val,
    )

    if verbose:
        print(f"[Mirador] Logged to {log_path}")

    return model_output, result.summary


# --- Backward compat for web server imports ---

# Keep MODEL_1 alias so mirador_web.py imports still work
MODEL_1 = MODEL


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Mirador Pipeline',
    )
    parser.add_argument(
        'prompt', nargs='?', default=None,
        help='Question to run through the pipeline',
    )
    parser.add_argument(
        '--npi', default=None,
        help='NPI to look up for pharmacy context',
    )
    parser.add_argument(
        '--log', default=str(DEFAULT_LOG),
        help='Path to log file',
    )
    parser.add_argument(
        '--interactive', action='store_true',
        help='Run in interactive mode (loop)',
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Suppress progress output',
    )
    args = parser.parse_args()

    from pharmacy_lookup import lookup_npi

    log_path = Path(args.log)
    verbose = not args.quiet
    pharmacy = None
    if args.npi:
        pharmacy = lookup_npi(args.npi)
        if not pharmacy:
            print(f"WARNING: NPI {args.npi} not found")

    if args.interactive:
        print("Mirador Pipeline")
        print(f"  Model: {MODEL}")
        print(f"  Log: {log_path}")
        if pharmacy:
            print(
                f"  Pharmacy: {pharmacy.get('npi')} "
                f"({pharmacy.get('pharmacy_name')})"
            )
        print("Type 'quit' or 'exit' to stop.\n")
        while True:
            try:
                question = input("Question> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break
            if not question:
                continue
            if question.lower() in ('quit', 'exit', 'q'):
                break
            m_out, v_out = run_pipeline(
                question, log_path, pharmacy, verbose,
            )
            print("\n--- MODEL OUTPUT ---")
            print(m_out)
            print("\n--- FACT VALIDATION ---")
            print(v_out)
            print()
    elif args.prompt:
        m_out, v_out = run_pipeline(
            args.prompt, log_path, pharmacy, verbose,
        )
        print("\n--- MODEL OUTPUT ---")
        print(m_out)
        print("\n--- FACT VALIDATION ---")
        print(v_out)
    else:
        if not sys.stdin.isatty():
            question = sys.stdin.read().strip()
            if question:
                m_out, v_out = run_pipeline(
                    question, log_path, pharmacy, verbose,
                )
                print("\n--- MODEL OUTPUT ---")
                print(m_out)
                print("\n--- FACT VALIDATION ---")
                print(v_out)
        else:
            parser.print_help()


if __name__ == '__main__':
    main()
