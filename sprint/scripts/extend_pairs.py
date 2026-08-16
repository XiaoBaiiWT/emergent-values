#!/usr/bin/env python3
"""
Extension run. For every pair already in results.jsonl, re-runs collect.py
at higher prices (20, 50, 100, 200) to find out whether the flat
installed-opposite curves ever actually cross 50% — or to get a much
stronger "still didn't move at 40x the alternative and 2x the entire
budget" result if they don't.

native_pref for each pair is read straight from the existing data (the
price_a=5 native row), not re-derived — so this works even though the
extended price list doesn't include 5.

Usage:
    python sprint/scripts/extend_pairs.py
"""

import json
import subprocess
import sys

EXISTING_RESULTS = "sprint/data/results.jsonl"
OPTIONS_PATH = "utility_analysis/shared_options/options_testing.json"
CATEGORY_FALLBACK = "Personal possessions"
EXTRA_PRICES = "20,50,100,200"


def load_existing_pairs(path):
    """
    Returns a dict keyed by (outcome_a, outcome_b) -> native_pref, built
    from each pair's native condition at price_a=5 in the existing data.
    """
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    pairs = {}
    for r in rows:
        if r.get("condition") != "native" or r.get("price_a") != 5:
            continue
        key = (r["outcome_a"], r["outcome_b"])
        native_pref = "A" if r["p_a"] > 0.5 else "B"
        pairs[key] = native_pref
    return pairs


def find_index(options, category, outcome_text):
    for idx, text in enumerate(options.get(category, [])):
        if text == outcome_text:
            return idx
    return None


def main():
    pairs = load_existing_pairs(EXISTING_RESULTS)
    print(f"Found {len(pairs)} pairs with a native price_a=5 row in {EXISTING_RESULTS}\n")

    with open(OPTIONS_PATH) as f:
        options = json.load(f)

    failures = []
    for (outcome_a, outcome_b), native_pref in pairs.items():
        category = None
        a_idx = b_idx = None
        for cat_name in options:
            a_idx = find_index(options, cat_name, outcome_a)
            b_idx = find_index(options, cat_name, outcome_b)
            if a_idx is not None and b_idx is not None:
                category = cat_name
                break
        if category is None:
            print(f"SKIP — couldn't find indices for pair: {outcome_a!r} / {outcome_b!r}", file=sys.stderr)
            failures.append((outcome_a, outcome_b))
            continue

        cmd = [
            sys.executable, "sprint/scripts/collect.py",
            "--category", category,
            "--a-idx", str(a_idx),
            "--b-idx", str(b_idx),
            "--prices", EXTRA_PRICES,
            "--native-pref", native_pref,
            "--output", "sprint/data/results_extended.jsonl",
        ]
        print(f"\n=== EXTEND: {a_idx} vs {b_idx} (native_pref={native_pref}) ===")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"  FAILED: {a_idx} vs {b_idx}", file=sys.stderr)
            failures.append((outcome_a, outcome_b))

    print(f"\nDone. {len(pairs) - len(failures)}/{len(pairs)} pairs extended.")
    if failures:
        print("Failed / skipped pairs:")
        for oa, ob in failures:
            print(f"  {oa[:40]} vs {ob[:40]}")
    print("\nNext: python sprint/scripts/analysis.py --input sprint/data/results_extended.jsonl "
          "--output-dir sprint/figures/extended --summary sprint/data/summary_extended.csv")


if __name__ == "__main__":
    main()