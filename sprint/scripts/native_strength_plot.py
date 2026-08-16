#!/usr/bin/env python3
"""
Native strength vs. price-sensitivity.
x-axis: how strongly the screener read the native preference at equal cost
y-axis: the fitted p* from the real price sweep (native condition only)

Uses data you already have — no new API calls. Joins:
  sprint/data/summary.csv              (from analysis.py on results.jsonl)
  sprint/data/screened_pairs_selected.json  (the screener's original reads)
"""

import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="sprint/data/summary.csv")
    parser.add_argument("--selected", default="sprint/data/screened_pairs_selected.json")
    parser.add_argument("--output", default="sprint/figures/native_strength_vs_pstar.png")
    args = parser.parse_args()

    summary = pd.read_csv(args.summary)
    native = summary[summary["condition"] == "native"].copy()

    with open(args.selected) as f:
        selected = json.load(f)
    all_pairs = [p for bucket in selected.values() for p in bucket]

    rows = []
    for p in all_pairs:
        label = f"{p['outcome_a'][:30]} vs {p['outcome_b'][:30]}"
        match = native[native["pair"] == label]
        if match.empty:
            print(f"WARN: no summary row found for {label!r} — skipping")
            continue
        row = match.iloc[0]
        rows.append({
            "pair": label,
            "screener_strength": p["strength"],
            "p_star_abs": row["p_star_abs"],
            "censored": row["censored"],
            "positive_beta1": row["positive_beta1"],
        })

    df = pd.DataFrame(rows)
    print(f"Matched {len(df)} of {len(all_pairs)} pairs between summary.csv and the screener's selection")

    plottable = df[df["p_star_abs"].notna() & ~df["censored"] & ~df["positive_beta1"]]
    unplottable = df[~df.index.isin(plottable.index)]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(plottable["screener_strength"], plottable["p_star_abs"],
               s=80, color="black", zorder=3, label="finite p* (plotted)")
    if not unplottable.empty:
        # Show these at strength on x, but flagged — don't invent a y-value
        for _, r in unplottable.iterrows():
            ax.annotate("censored/broken", (r["screener_strength"], 0),
                        fontsize=7, color="crimson", rotation=90, va="bottom")
        ax.scatter(unplottable["screener_strength"], [0] * len(unplottable),
                   marker="x", color="crimson", s=60, zorder=3,
                   label="censored or broken (no real p*)")

    ax.set_xlabel("Screener-read native preference strength (0.5-1.0)")
    ax.set_ylabel("Fitted native p* (absolute price)")
    ax.set_title("Native price-sensitivity vs. native preference strength")
    ax.legend()
    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"Saved: {args.output}")
    print(f"\n{len(plottable)} plottable, {len(unplottable)} censored/broken (shown separately, not faked)")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
