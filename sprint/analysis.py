#!/usr/bin/env python3
"""
Sprint analysis script — CORRECTED (v2).
Reads JSONL, fits probit, extracts p* with CIs, flags positive β₁,
applies censoring rule, classifies scenarios, AND surfaces the
held/switched/indifferent state that collect.py already computes
per price level (this was being collected but never reported).
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from statsmodels.discrete.discrete_model import Probit


def fit_probit(price_diffs, p_as, n_totals):
    y, X = [], []
    for diff, p_a, n_tot in zip(price_diffs, p_as, n_totals):
        n_a = int(round(p_a * n_tot))
        n_b = n_tot - n_a
        y.extend([1] * n_a + [0] * n_b)
        X.extend([[1, diff]] * n_tot)

    y = np.array(y)
    X = np.array(X)

    try:
        model = Probit(y, X)
        result = model.fit(disp=0, maxiter=100)
    except Exception as e:
        return {
            "converged": False, "error": str(e),
            "beta0": None, "beta1": None,
            "p_star_diff": None, "p_star_abs": None,
            "censored": True, "positive_beta1": False,
            "ci_beta0": [None, None], "ci_beta1": [None, None],
        }

    beta0, beta1 = result.params
    ci = result.conf_int(alpha=0.05).values

    censored = bool(ci[1, 0] <= 0 <= ci[1, 1])
    positive_beta1 = bool(beta1 > 0)

    if censored or positive_beta1 or abs(beta1) < 1e-8:
        p_star_diff = None
        p_star_abs = None
    else:
        p_star_diff = -beta0 / beta1
        p_star_abs = 5.0 + p_star_diff

    return {
        "converged": True,
        "error": None,
        "beta0": float(beta0),
        "beta1": float(beta1),
        "p_star_diff": float(p_star_diff) if p_star_diff is not None else None,
        "p_star_abs": float(p_star_abs) if p_star_abs is not None else None,
        "censored": censored,
        "positive_beta1": positive_beta1,
        "ci_beta0": [float(ci[0, 0]), float(ci[0, 1])],
        "ci_beta1": [float(ci[1, 0]), float(ci[1, 1])],
        "aic": float(result.aic),
    }


def plot_pair(df_pair, pair_label, out_dir):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = {"native": "black", "installed_opposite": "crimson", "placebo": "gray"}
    price_grid = np.linspace(-4, 15, 200)

    for condition, group in df_pair.groupby("condition"):
        color = colors.get(condition, "blue")
        diffs = (group["price_a"] - group["price_b"]).values
        p_as = group["p_a"].values
        n_totals = group["n_total"].values

        ax.scatter(diffs, p_as, color=color, s=80, zorder=3, label=condition)

        fit = fit_probit(diffs.tolist(), p_as.tolist(), n_totals.tolist())
        # Reuse the already-fitted beta0/beta1 instead of refitting a second
        # time — same math, no duplicate optimizer call.
        if fit["converged"] and not fit["censored"] and not fit["positive_beta1"]:
            fitted = norm.cdf(fit["beta0"] + fit["beta1"] * price_grid)
            ax.plot(price_grid, fitted, color=color, linewidth=2, alpha=0.7)

            ps = fit["p_star_diff"]
            if ps is not None and -5 <= ps <= 20:
                ax.axvline(ps, color=color, linestyle="--", alpha=0.4)
                ax.text(ps, 0.55, f"p*={ps:.1f}", color=color, fontsize=8, rotation=90, va="bottom")

    ax.axhline(0.5, color="lightgray", linestyle="--", zorder=0)
    ax.axvline(0, color="lightgray", linestyle=":", zorder=0)
    ax.set_xlabel("Price difference (c_A − c_B)")
    ax.set_ylabel("P(choose A)")
    ax.set_title(pair_label)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="best")
    plt.tight_layout()

    fname = pair_label.replace(" ", "_").replace("/", "_")[:50] + ".png"
    fpath = os.path.join(out_dir, fname)
    plt.savefig(fpath, dpi=150)
    plt.close()
    return fpath


def fmt_fit(row):
    if row["positive_beta1"]:
        return "**BROKEN** (β₁ > 0 — price sensitivity backwards)"
    if row["censored"]:
        if row.get("error"):
            return f"**DID NOT CONVERGE** ({row['error']})"
        return "**CENSORED** (brittle rule, β₁ CI includes 0)"
    ps = row["p_star_abs"]
    if ps is None:
        return "undefined"
    return f"{ps:.2f} units"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="sprint/data/friday_results.jsonl")
    parser.add_argument("--output-dir", default="sprint/figures")
    parser.add_argument("--summary", default="sprint/data/summary.csv")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.summary) or ".", exist_ok=True)

    records = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    df = pd.DataFrame(records)
    print(f"Loaded {len(df)} trials")
    has_state = "state" in df.columns

    df["price_diff"] = df["price_a"] - df["price_b"]

    rows = []
    pair_keys = df.groupby(["outcome_a", "outcome_b"]).size().reset_index()[["outcome_a", "outcome_b"]]

    for _, (oa, ob) in pair_keys.iterrows():
        pair_label = f"{oa[:30]} vs {ob[:30]}"
        mask = (df["outcome_a"] == oa) & (df["outcome_b"] == ob)
        df_pair = df[mask].copy()
        plot_path = plot_pair(df_pair, pair_label, args.output_dir)

        for condition, group in df_pair.groupby("condition"):
            diffs = group["price_diff"].values
            p_as = group["p_a"].values
            n_totals = group["n_total"].values

            fit = fit_probit(diffs.tolist(), p_as.tolist(), n_totals.tolist())

            state_counts = {"held": 0, "switched": 0, "indifferent": 0}
            if has_state:
                state_counts.update(group["state"].value_counts().to_dict())

            rows.append({
                "pair": pair_label,
                "condition": condition,
                "n_trials": len(group),
                "beta0": fit["beta0"],
                "beta1": fit["beta1"],
                "censored": fit["censored"],
                "positive_beta1": fit["positive_beta1"],
                "error": fit.get("error"),
                "p_star_diff": fit["p_star_diff"],
                "p_star_abs": fit["p_star_abs"],
                "ci_beta1_low": fit["ci_beta1"][0],
                "ci_beta1_high": fit["ci_beta1"][1],
                "n_held": state_counts.get("held", 0),
                "n_switched": state_counts.get("switched", 0),
                "n_indifferent": state_counts.get("indifferent", 0),
                "plot": plot_path,
            })

    summary = pd.DataFrame(rows)
    summary.to_csv(args.summary, index=False)
    print(f"\nSummary written to {args.summary}")

    print("\n" + "=" * 70)
    print("DESCRIPTIVE REPORT")
    print("=" * 70)

    for pair in summary["pair"].unique():
        print(f"\n## {pair}")
        sub = summary[summary["pair"] == pair]
        native = sub[sub["condition"] == "native"]
        inst = sub[sub["condition"] == "installed_opposite"]
        placebo = sub[sub["condition"] == "placebo"]

        for label, r in [("Native", native), ("Installed-opposite", inst), ("Placebo", placebo)]:
            if r.empty:
                continue
            row = r.iloc[0]
            state_str = ""
            if has_state:
                state_str = f"  [held={row['n_held']} switched={row['n_switched']} indifferent={row['n_indifferent']}]"
                if row["n_switched"] > 0 and row["n_indifferent"] > 0:
                    state_str += "  <- both present, check they weren't conflated"
            print(f"  {label:<20}{fmt_fit(row)}{state_str}")

        if not native.empty and not inst.empty:
            n = native.iloc[0]
            i = inst.iloc[0]
            if i["positive_beta1"]:
                scenario = "BROKEN — positive β₁, check data"
            elif i["censored"]:
                scenario = "SCENARIO 3 — Brittle rule (ignores cost)"
            elif i["p_star_abs"] is not None and n["p_star_abs"] is not None:
                ratio = i["p_star_abs"] / n["p_star_abs"] if n["p_star_abs"] != 0 else float("inf")
                if i["p_star_abs"] < 2.0:
                    scenario = "SCENARIO 2 — Superficial compliance (collapses immediately)"
                elif 0.5 <= ratio <= 2.0:
                    scenario = "SCENARIO 1 — Real utility integration (comparable to native)"
                else:
                    scenario = f"Intermediate (installed={i['p_star_abs']:.1f}, native={n['p_star_abs']:.1f})"
            else:
                scenario = "Cannot classify (missing values)"
            print(f"  -> {scenario}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()