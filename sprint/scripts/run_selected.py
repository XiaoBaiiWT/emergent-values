#!/usr/bin/env python3
"""
Orchestrator. Reads the stratified pair list screener.py produced and
runs collect.py once per pair, appending everything into one JSONL.
Placebo is only attached to a handful of pairs (~5 total), per design.

Usage (run from repo root, after screener.py has produced its output):
    python sprint/scripts/run_selected.py
"""

import json
import subprocess
import sys

SELECTED_PATH = "sprint/data/screened_pairs_selected.json"
OUTPUT_PATH = "sprint/data/results.jsonl"
CATEGORY_FALLBACK = "Personal possessions"

# ~5 placebo trials spread across strata, not all 20 pairs
PLACEBO_PER_STRATUM = {"weak": 2, "moderate": 2, "strong": 1}


def main():
    with open(SELECTED_PATH) as f:
        selected = json.load(f)

    total = sum(len(v) for v in selected.values())
    print(f"Running collect.py on {total} pairs -> {OUTPUT_PATH}\n")

    failures = []
    for stratum, pairs in selected.items():
        placebo_budget = PLACEBO_PER_STRATUM.get(stratum, 0)
        for idx, pair in enumerate(pairs):
            category = pair.get("category", CATEGORY_FALLBACK)
            a_idx, b_idx = pair["a_idx"], pair["b_idx"]
            run_placebo = idx < placebo_budget

            cmd = [
                sys.executable, "sprint/scripts/collect.py",
                "--category", category,
                "--a-idx", str(a_idx),
                "--b-idx", str(b_idx),
                "--output", OUTPUT_PATH,
            ]
            if run_placebo:
                cmd.append("--placebo")

            tag = f"[{stratum}] {a_idx} vs {b_idx}" + (" (+placebo)" if run_placebo else "")
            print(f"\n=== {tag} ===")
            result = subprocess.run(cmd)
            if result.returncode != 0:
                print(f"  FAILED: {tag} — continuing with remaining pairs", file=sys.stderr)
                failures.append(tag)

    print(f"\nDone. {total - len(failures)}/{total} pairs succeeded.")
    if failures:
        print("Failed pairs (rerun these manually):")
        for f in failures:
            print(f"  {f}")
    print(f"\nNext: python sprint/scripts/analysis.py --input {OUTPUT_PATH}")


if __name__ == "__main__":
    main()