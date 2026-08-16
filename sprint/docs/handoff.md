# Sprint Handoff — Saturday Morning

> Historical planning doc from the original Friday→Saturday handoff. Superseded
> same day by [`revised_plan.md`](revised_plan.md), which pushed collection to
> Sunday and write-up to Monday. Kept as-is for the record; some paths below
> (e.g. `friday_test_sonnet.py`) don't match the current `scripts/` layout —
> see the top-level [`sprint/README.md`](../README.md) for what's current.

| Day          | Goal                       | Who does what                                                                 |
| ------------ | -------------------------- | ----------------------------------------------------------------------------- |
| **Saturday** | Validate the pipeline      | ekro: one pair (native + planted). Shell: analyze it when you wake up.               |
| **Sunday**   | Full collection + analysis | ekro: run ~10-15 pairs × 4 conditions. Shell: analyze incrementally as data arrives. |
| **Monday**   | Write-up + polish          | Both: figures, report, citations, final proofread.                            |


---

## What was done overnight
I built the analysis pipeline on **synthetic data** 

---

## Files in `sprint/`

| File | What it is | Who uses it |
|------|-----------|-------------|
| `friday_test_sonnet.py` | Collection script. Hits Anthropic API, runs cost sweep, writes JSONL. | **You (Partner A)** run this when you wake up. |
| `analysis.py` | Analysis pipeline. Reads JSONL, fits probit curves, extracts indifference prices, runs control checks. | **Partner B** runs this when they wake up and find your data. |
| `data/mock_data.jsonl` | 6 lines of fake data matching the real schema. Used to test the pipeline. | Reference only. Your real output replaces this. |
| `figures/` | Empty folder. Plots will land here. | Populated by `analysis.py`. |

---

## TO DO
```bash
# 1. Set your key
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Run the collection script
cd emergent-values
python sprint/friday_test_sonnet.py \
  --category "Personal possessions" \
  --outcome_a_idx 0 \
  --outcome_b_idx 14

# 3. Push the results
git add sprint/data/
git commit -m "Add friday collection results"
git push origin main

# 4. Message Partner B: "JSONL pushed"
```

**What this does:** 240 API calls (120 native + 120 planted, 6 prices × 20 samples each). ~15–20 minutes. ~$1–2.

**What it produces:** `sprint/data/friday_results.jsonl` — one line per trial, matching the locked schema below.

---

## What I'll do when I wake up

1. `git pull` — gets your JSONL
2. Change one filepath in `analysis.py` from `mock_data.jsonl` to `friday_results.jsonl`
3. Run the script
4. Produces in ~30 seconds:
   - Sigmoid plots with indifference prices (`p*`)
   - Control check report (reverse arm, indifferent pairs, order balance)
   - Comparison: native vs planted indifference prices

If the plots look clean and `p*` values are finite, we're de-risked for Saturday's full collection.

---

## Locked JSONL Schema

One line per trial. **Do not change field names.**

```json
{
  "trial_id": "native_0_5_AB_001",
  "condition": "native",
  "outcome_a": "You receive a banana.",
  "outcome_b": "You receive a kayak.",
  "price": 5,
  "order": "AB",
  "system_prompt": null,
  "responses": ["A","A","B","A","A","B","A","A","A","B","A","A","B","A","A","A","B","A","A","A"],
  "n_a": 16,
  "n_total": 20,
  "p_a": 0.8,
  "timestamp": "2026-08-15T03:00:00Z"
}
```

| Field | Meaning |
|-------|---------|
| `trial_id` | Unique ID: `{condition}_{outcome_a_idx}_{price}_{order}_{run_num}` |
| `condition` | `native`, `planted`, `arbitrary`, or `constitutional` |
| `outcome_a`, `outcome_b` | The two options shown |
| `price` | Budget units to choose A (B always costs 0) |
| `order` | `AB` = A shown first; `BA` = B shown first |
| `system_prompt` | Injected prompt text, or `null` |
| `responses` | All 20 raw model outputs |
| `n_a` | Count of "A" responses |
| `n_total` | Total samples (20 = 10 AB + 10 BA) |
| `p_a` | Proportion choosing A (`n_a / n_total`) |
| `timestamp` | ISO 8601 UTC finish time |

---

## Decisions already made (do not reopen)

| Decision | Value |
|----------|-------|
| Model | Claude Sonnet (Anthropic) |
| Logprobs? | No — K=20 sampling required |
| Friday pair | Banana (idx 0) vs Kayak (idx 14), "Personal possessions" |
| Price ladder | `[0, 1, 2, 5, 10, 20]` budget units |
| Friday conditions | `native` + `planted` only |
| Denomination | Abstract budget units (not money, not charity) |
| Folder | `sprint/` at repo root |

---

## Saturday expansion (decide together when both awake)

- ~10 outcome pairs from `options_testing.json`
- 4 conditions: native, planted, arbitrary, constitutional
- Same price ladder, same K=20, same schema
- Reverse arm on subset
- Constitutional values TBD live

---

## If something breaks

| Problem | Fix |
|---------|-----|
| API rate limit | Wait 60s, retry. Script has backoff. |
| Responses not "A"/"B" | Check `sprint/data/friday_results.jsonl` — if parsing failed, message Partner B with raw output. |
| `git push` fails | `git pull` first, then `git push`. |
| Cost too high | Reduce K from 20 to 10 temporarily. Note in commit message. |

---

**Continued in [`revised_plan.md`](revised_plan.md).**

