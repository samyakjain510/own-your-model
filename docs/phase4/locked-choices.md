# Choices locked before opening the test set (2026-11-23)

Everything below was decided on dev only. The sealed test set (`test_v2`, 800 complaints, Apr 1 – Aug 14 2026, sha256 `ccec1cfb…27afe`) is opened after this file is committed, and nothing here changes after that.

## Contestants

| Role | Model and setup | Why this one |
|---|---|---|
| Own (main) | Qwen3-4B-Instruct-2507 + LoRA trained on 8,000 examples (adapter from Kaggle job `oym-qwen3-4b-b`), greedy decoding, short prompt | Best on dev |
| Own (learning curve) | Same base, LoRA on 500 and 2,000; base model with no training and the label-list prompt | Shows how much data it takes |
| Rent (main) | Claude Haiku 5.5, prompt `route-v2` (label list, company name, routing rule), default effort, 10 complaints per call, seed 0 | Best Haiku setup on dev. Low effort scored 12 points lower on product and issue; worked examples (`route-v3`) scored 3.7 lower (interval −8.3 to +1.0) |
| Rent (reference) | Claude Sonnet 5.5, same prompt and settings | A stronger rented model, for context. Not tuned on dev |

## Label checker

Claude Opus 5.5, system prompt sha256 `165026a5…a574`, default effort, 10 per call. It reads each test complaint with its logged label only. It's tested on dev with planted errors: it caught 96% of wrong products and 86% of wrong issues, and it flagged 22% of untouched labels.

## Scores

- Product accuracy and product-and-issue accuracy, exact match, missing answers count as wrong, Wilson 95% intervals.
- Head-to-head: paired bootstrap of the accuracy difference on the same complaints, 2,000 resamples, seed 0.
- Three views: logged labels (primary), only labels the checker accepted, and logged-or-checker label counts.
- **Primary comparison:** the 8,000-example model minus Haiku `route-v2`, product-and-issue accuracy, logged labels, all 800 test complaints.

## Cost

`src/oym/cost.py` with `configs/cost_inputs.json` as committed today, using the tokens measured on the test run and the T4 speed from `runs/kaggle/oym-bench-hf-qwen3-4b-n8000` (2.40 complaints a second).
