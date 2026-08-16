# Revised Sprint Plan — Deadline: Monday

> Split out from `handoff.md`, where this had been pasted in as an unclosed
> shell heredoc (`cat > sprint/REVISED_PLAN.md << 'EOF'`) instead of landing
> in its own file. Content is unchanged.

**Written:** Saturday 3:47 AM
**Partner B:** About to sleep (analysis pipeline pushed)
**Partner A:** Asleep (will wake up to `handoff.md`)
**Deadline:** Monday (2.5 days remaining at time of writing)

---

## Why this changes everything

Old plan: Crush everything into Friday night + Saturday. High risk, no buffer.
**New plan:** Saturday = validation, Sunday = collection, Monday = analysis + write-up. Sustainable.

---

## Saturday (today) — Validate the Pipeline

**Morning (Partner A wakes up):**
- Run `friday_test_sonnet.py` on one pair (banana vs kayak)
- Native + Planted, 6 prices, K=20
- Push JSONL, message Partner B
- **Goal:** Confirm the API works, the schema is correct, and the model returns parseable "A"/"B"

**Afternoon (both awake):**
- Partner B pulls JSONL, runs `analysis.py`
- **Merge test:** Do the plots look sane? Is `p*` finite? Do native and planted differ?
- If YES: pipeline is validated. Plan Sunday's full design.
- If NO: debug together. You have time.

**Evening:**
- Finalize Saturday scope (~10-15 pairs, 4 conditions)
- Design constitutional prompts (decide together live)
- Pick indifferent pairs for control
- Partner A preps the collection script for Sunday loops

---

## Sunday — Full Data Collection

**All day (Partner A):**
- Run full collection: ~10-15 pairs × 4 conditions × 6 prices × 2 orders
- Estimated API calls: 5,760–8,640 (15 pairs × 4 × 6 × 2 × 20 samples)
- Estimated cost: ~$30–50 on Sonnet
- **Write every result to disk as it arrives.** Never re-run a completed cell.
- Push JSONL to repo every ~2 hours so Partner B can analyze incrementally

**In parallel (Partner B):**
- Ingest partial JSONL as it arrives
- Fit probits, generate plots
- Run control checks on completed pairs
- Flag anomalies early (e.g., probit not converging, p* negative)
- Build the figure set for the report

**Evening:**
- Collection complete
- Full analysis run
- Both review: Do results make sense? Do we need more pairs?

---

## Monday — Analysis, Write-up, Polish

**Morning:**
- Final analysis pass on complete dataset
- Generate all figures (sweep curves, p* comparison table, control check report)
- Decide if effort-based robustness check is feasible (if Sunday went well)

**Afternoon:**
- Write the report:
  - Introduction (hook: can prompting write to utility functions?)
  - Methods (price sweep, probit fitting, 3 controls)
  - Results (p* values per condition, comparison table)
  - Discussion (what it means for alignment)
- Add citations to Mazeika et al. paper

**Evening:**
- Polish figures
- Final proofread
- Submit / present

---

> Saturday is just validation — one pair, native + planted. Push the JSONL when done. I'll analyze it when I wake up. If it works, we plan Sunday's full collection together. No rush.

---

## Risk mitigation with Monday buffer

| Risk | Old plan (Sat only) | New plan (Mon deadline) |
|------|---------------------|------------------------|
| API down Saturday | Catastrophic | Switch to backup model Sunday |
| Probit doesn't converge | No time to debug | Iterate Sunday morning |
| Constitutional prompts don't work | Skip condition | Redesign Sunday afternoon |
| Need more pairs | Can't collect | Sunday extension possible |
| Figures ugly | Submit anyway | Monday polish day |

---

## Updated Saturday task list for Partner A

1. Set API key
2. Run: `python sprint/friday_test_sonnet.py --category "Personal possessions" --outcome_a_idx 0 --outcome_b_idx 14`
3. Push JSONL
4. Message B: "JSONL pushed, pipeline works" OR "JSONL pushed, [describe issue]"
5. **Sleep or relax.** Full collection is Sunday.

---

## Updated Saturday task list for Partner B (when you wake up)

1. Pull repo
2. Run `analysis.py` on `friday_results.jsonl`
3. Check: plots sane? p* finite? native vs planted differ?
4. Message A with results
5. **If validation passes:** Plan Sunday's full design together (pair selection, constitutional prompts)
6. **If validation fails:** Debug with A

---

## The constitutional condition (decide Saturday evening)

With Monday buffer, you can actually design this properly:

| Approach | Prompt example |
|----------|---------------|
| World-state framing | "A world where you consistently tell the truth" vs "A world where you receive a kayak" |
| Behavioral commitment | "You are honest even when costly" as system prompt, then banana vs kayak |

Test both on Sunday morning with 2-3 pairs. Keep whichever produces cleaner indifference curves.

---

## Bottom line

**Saturday = one pair, prove it works.**
**Sunday = collect everything.**
**Monday = analyze and write.**
