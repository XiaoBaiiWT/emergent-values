# Sprint: Can prompting write to a model's utility function?

Weekend pipeline extending the [Utility Engineering](../README.md) methodology:
elicit an LLM's *native* revealed preference between two outcomes via a price
sweep, then see whether a *planted* system prompt (naming the outcome text
directly) can shift the indifference price — vs. arbitrary/constitutional
prompts as controls. See [`docs/handoff.md`](docs/handoff.md) and
[`docs/revised_plan.md`](docs/revised_plan.md) for the original plan and
schedule.

## Layout

```
sprint/
├── scripts/     Pipeline code, run from the repo root
├── data/        Pipeline inputs/outputs (current, live data only)
│   └── archive/ Superseded or invalid runs — not used by any script default
├── figures/     Plots from analysis.py (git-ignored contents; folder tracked via .gitkeep)
└── docs/        Planning / handoff notes
```

## Pipeline

Run in this order, from the repo root:

1. **`scripts/screener.py`** — Tests candidate outcome pairs at equal cost
   (5 vs 5) and stratifies them by native-preference strength (weak /
   moderate / strong) so the final pair set isn't all near-50/50.
   Writes `data/screened_pairs.json` (all candidates) and
   `data/screened_pairs_selected.json` (the stratified picks — currently
   5 weak / 4 moderate / 7 strong).

2. **`scripts/run_selected.py`** — Orchestrator. Reads
   `data/screened_pairs_selected.json` and calls `collect.py` once per pair,
   appending everything into `data/results.jsonl`. Attaches a placebo
   condition to a handful of pairs per stratum.

3. **`scripts/collect.py`** — Does the actual API calls for one pair: native
   sweep, installed-opposite (planted) condition, and optional placebo.
   Appends JSONL incrementally so a crash mid-run doesn't lose data.

4. **`scripts/extend_pairs.py`** — Follow-up pass. For every pair already in
   `data/results.jsonl`, re-runs `collect.py` at much higher prices (20,
   50, 100, 200) to check whether flat installed-opposite curves ever
   cross 50%. Writes `data/results_extended.jsonl`.

5. **`scripts/analysis.py`** — Reads a results JSONL, fits probit curves,
   extracts indifference prices (`p*`) with confidence intervals, and runs
   the control checks (reverse arm, indifferent pairs, order balance).
   Writes plots to `figures/` and a summary CSV to `data/`.

All scripts default to repo-root-relative paths (e.g. `sprint/data/...`), so
invoke them as `python sprint/scripts/<name>.py` from the repo root, not from
inside `sprint/`.

## Data

- **`data/results.jsonl`** — the live dataset (217 trials as of last count):
  native-condition price sweeps across the screened pairs.
- **`data/screened_pairs.json`** / **`screened_pairs_selected.json`** —
  pair-selection artifacts from `screener.py`, not trial data.
- **`data/archive/mock_data.jsonl`** — 6 lines of synthetic data matching the
  schema, used only to smoke-test `analysis.py` before real data existed.
  No longer referenced by any script default.
- **`data/archive/INVALID_price_bug_friday_results.jsonl`** — an early
  collection run with a known letter-swap bug in the prompt builder (fixed
  in the current `collect.py`/`screener.py`, per their "CORRECTED" docstrings).
  Kept for reference; do not feed into `analysis.py`.
