#!/usr/bin/env python3
"""
Mirador Chain-of-Thought Pipeline
===================================
Model 1 (rmm-pharmacy-expert) --> Model 2 (rmm-chain-analyst)

Emulates the Mirador framework: domain expert produces structured
analysis, then a chain-of-thought reasoner synthesizes, challenges,
and deepens the output. All runs cataloged to a .txt log file with
full chain-of-thought traces.

Usage:
  python3 mirador_chain.py "Your question here"
  python3 mirador_chain.py --prompt "Your question" --log custom_log.txt
  python3 mirador_chain.py --interactive

The log file captures every run with timestamps, model identifiers,
full prompts, full responses (including <think> blocks from DeepSeek),
and chain metadata.
"""

import argparse
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path


# --- Configuration ---

MODEL_1 = 'rmm-pharmacy-expert'
MODEL_2 = 'rmm-chain-analyst'
DEFAULT_LOG = Path(__file__).resolve().parent / 'mirador_chain_log.txt'

CHAIN_PROMPT_TEMPLATE = textwrap.dedent("""\
    === ORIGINAL QUESTION ===
    {question}

    === MODEL 1 OUTPUT (rmm-pharmacy-expert) ===
    {model1_output}

    === YOUR TASK ===
    Apply your 5-step analysis framework. Check every number \
    against your reference data. Flag anything fabricated. \
    What should the outreach team actually do?
""")


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
    m1_output: str,
    m2_prompt: str,
    m2_output: str,
    elapsed_m1: float,
    elapsed_m2: float,
) -> None:
    """Append a full chain run to the log file."""
    sep = '=' * 72
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n{sep}\n")
        f.write(f"MIRADOR CHAIN RUN: {run_id}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Model 1: {MODEL_1}\n")
        f.write(f"Model 2: {MODEL_2}\n")
        f.write(f"M1 elapsed: {elapsed_m1:.1f}s\n")
        f.write(f"M2 elapsed: {elapsed_m2:.1f}s\n")
        f.write(f"Total elapsed: {elapsed_m1 + elapsed_m2:.1f}s\n")
        f.write(f"{sep}\n\n")

        f.write("--- QUESTION ---\n")
        f.write(f"{question}\n\n")

        f.write(f"--- MODEL 1 OUTPUT ({MODEL_1}) ---\n")
        f.write(f"{m1_output}\n\n")

        f.write(f"--- MODEL 2 PROMPT (fed to {MODEL_2}) ---\n")
        f.write(f"{m2_prompt}\n\n")

        f.write(f"--- MODEL 2 OUTPUT ({MODEL_2}) ---\n")
        f.write("(includes full chain-of-thought / <think> blocks)\n\n")
        f.write(f"{m2_output}\n\n")

        f.write(f"{sep}\n")
        f.write("END OF RUN\n")
        f.write(f"{sep}\n\n")


# --- Chain Execution ---

def run_chain(
    question: str,
    log_path: Path,
    verbose: bool = True,
) -> tuple[str, str]:
    """Execute the full Mirador chain.

    Returns (model1_output, model2_output).
    """
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    if verbose:
        print(f"[Mirador] Run {run_id}")
        print(f"[Mirador] Question: {question[:80]}...")
        print(f"[Mirador] Stage 1: {MODEL_1}...")

    t0 = datetime.now()
    m1_output = run_model(MODEL_1, question, timeout=300)
    t1 = datetime.now()
    elapsed_m1 = (t1 - t0).total_seconds()

    if verbose:
        print(f"[Mirador] Stage 1 complete ({elapsed_m1:.1f}s)")
        print(f"[Mirador] Stage 2: {MODEL_2} (chain-of-thought)...")

    m2_prompt = CHAIN_PROMPT_TEMPLATE.format(
        question=question,
        model1_output=m1_output,
    )

    t2 = datetime.now()
    m2_output = run_model(MODEL_2, m2_prompt, timeout=600)
    t3 = datetime.now()
    elapsed_m2 = (t3 - t2).total_seconds()

    if verbose:
        print(f"[Mirador] Stage 2 complete ({elapsed_m2:.1f}s)")
        print(f"[Mirador] Total: {elapsed_m1 + elapsed_m2:.1f}s")

    log_run(
        log_path, run_id, question,
        m1_output, m2_prompt, m2_output,
        elapsed_m1, elapsed_m2,
    )

    if verbose:
        print(f"[Mirador] Logged to {log_path}")

    return m1_output, m2_output


# --- Main ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Mirador Chain-of-Thought Pipeline',
    )
    parser.add_argument(
        'prompt', nargs='?', default=None,
        help='Question to run through the chain',
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

    log_path = Path(args.log)
    verbose = not args.quiet

    if args.interactive:
        print("Mirador Chain-of-Thought Pipeline")
        print(f"  Model 1: {MODEL_1}")
        print(f"  Model 2: {MODEL_2}")
        print(f"  Log: {log_path}")
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
            m1_out, m2_out = run_chain(
                question, log_path, verbose,
            )
            print("\n--- MODEL 1 (Domain Expert) ---")
            print(m1_out)
            print("\n--- MODEL 2 (Chain-of-Thought Synthesis) ---")
            print(m2_out)
            print()
    elif args.prompt:
        m1_out, m2_out = run_chain(
            args.prompt, log_path, verbose,
        )
        print("\n--- MODEL 1 (Domain Expert) ---")
        print(m1_out)
        print("\n--- MODEL 2 (Chain-of-Thought Synthesis) ---")
        print(m2_out)
    else:
        if not sys.stdin.isatty():
            question = sys.stdin.read().strip()
            if question:
                m1_out, m2_out = run_chain(
                    question, log_path, verbose,
                )
                print("\n--- MODEL 1 (Domain Expert) ---")
                print(m1_out)
                print("\n--- MODEL 2 (Chain-of-Thought) ---")
                print(m2_out)
        else:
            parser.print_help()


if __name__ == '__main__':
    main()
