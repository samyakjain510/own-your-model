# Dataset card: CFPB complaint routing (training sets v1)

**Built by:** `src/oym/trainset.py`, seed 7, on 2026-11-22. Numbers below come from `data/train/manifest.json`.

## What it is

Chat-format examples for routing a consumer finance complaint to a CFPB **product** and **issue**. Input: the company named on the complaint plus the complaint text (PII-scrubbed, cut to 500 words). Target: `{"product": ..., "issue": ...}`.

## Where it comes from

- CFPB Consumer Complaint Database, Narratives Archive ZIPs (public; API metadata tags the data CC0). Complaints received **2025-09-01 to 2026-02-28** (326,813 with text).
- Labels are the product and issue **the consumer picked** when filing. Nobody relabeled them by hand. Where identical texts were filed several times, the most common label among the copies was used (this changed 378 labels).

## Processing

1. Exact copies collapsed: 326,813 complaints became 187,657 unique texts. About half the complaints in this window are copies, mostly template letters.
2. Decontamination against `dev_v1` and `test_v2` (1,600 complaints from Apr to Aug 2026): 0 exact matches, 6 near-copies dropped (MinHash, Jaccard ≥ 0.8). A second, independent overlap check on the final pool passed.
3. Near-copies inside the training pool dropped: 456.
4. Regex PII scrub on top of CFPB's own redaction (`src/oym/pii.py`). Its miss rate isn't measured yet.
5. Nested sets: `train_500` ⊂ `train_2000` ⊂ `train_8000`; separate `val` (300).

## Product mix (train_8000)

Credit reporting 3,406 · Debt collection 1,419 · Credit card 907 · Checking or savings 843 · Money transfer 433 · Mortgage 314 · others smaller. The test window's mix is very different (credit reporting is ~3% there), and that's deliberate: we train on the recent past the way a real team would, and measure what the shift costs.

## Known limits

- Consumer labels are noisy. Identical texts in this window agree on product+issue 90.6% of the time (`runs/noise/dup_agreement_recent_6mo.json`), and unique complaints may agree less.
- Residual PII: CFPB says its scrubbing reduces risk without removing it.
- Text isn't redistributed. We publish complaint IDs (`data/train/*.ids.txt`) and the build script; the text is downloaded from CFPB.
