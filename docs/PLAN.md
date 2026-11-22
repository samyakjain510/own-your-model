# Plan

Last updated 2026-11-22.

## The question

For one narrow, high-volume job, can a small open model trained on a company's own logs do the job about as well as a rented frontier model? If yes, at what volume does owning it get cheaper than renting?

The job in this case study: read a consumer's complaint about a financial product and route it. That means picking the product (credit card, mortgage, debt collection...) and the issue (billing dispute, wrong info on a credit report...). Data: the CFPB Consumer Complaint Database, which is US government data in the public domain.

## Scope (version 1)

- **User:** an engineer or technical PM at a company with one narrow, high-volume job, asked "could we do this cheaper or in-house?"
- **Input:** their logs (past inputs plus the decision made) and a ~10-line config: input column, decision columns, monthly volume, models to compare, hardware and staff costs.
- **Output:** a scorecard on their own data with intervals, trained adapters, and a one-page decision with break-even volume and remaining failure cases.
- **Version 1 covers only pick-from-a-list jobs** (routing, tagging, multi-field classification), where code can grade answers. Free-text jobs (replies, summaries) need a human-checked AI judge and are left for later.
- The CFPB case study is the kit's first user. See `docs/learn/01-what-the-kit-does.md`.

## Ground rules

- **$0 spend.** No API keys and no paid GPUs. Claude runs through the Claude Code subscription in headless mode (`claude -p`). Training runs on free Kaggle or Colab GPUs, or on the M4 Mac with MLX. Cost figures for paid options come from published price lists and are never bought.
- **No new human labels.** Nobody hand-labels anything for this project. Ground truth comes from the human decisions already in the logs (the consumer picked the product and issue when filing). Any label Claude adds or changes is marked as Claude's and reported that way.
- **No model grades its own work.** Claude's baseline is always scored against the original logged labels, never against labels Claude helped make.
- **Every number comes from a saved run** with its config, data hash and seed under `runs/`.
- Clean room: no code, ideas or files from any prior school project.

## How we get an answer key without hand-labeling

The logged labels are human labels, but noisy ones: consumers sometimes pick the wrong product, or a complaint covers two products. So the kit keeps two views of the test set.

1. **As logged.** The consumer's original labels, untouched. No model touches this answer key, so it's fair to every model, Claude included.
2. **Audited.** The same items minus the ones an auditor flags as mislabeled or ambiguous. Items are removed, never relabeled.

The auditor is an LLM judge. To check whether we can trust it without human labels, we plant errors: we swap the label on a set of items to a wrong one on purpose and measure how often the auditor catches the swap (true positive rate). We also measure how often it leaves correct labels alone (true negative rate) on items where several independent signals agree the label is right. We report both rates with confidence intervals. If the auditor can't catch planted errors reliably, we don't use it.

## Phases

| Phase | What happens | Output |
|---|---|---|
| 0. Research | Competitors, prior work, dataset license, models and free compute | `docs/phase0/*.md` |
| 1. Logs → traces | Loader, PII scrub with a measured miss rate, one-command quickstart | `python -m oym quickstart` |
| 2. Errors → eval | Run Claude on a sample, open-code failures, build a failure taxonomy, freeze a time-split test set, run leakage checks, write code checks, calibrate the auditor on planted errors | `evals/`, test set, judge report |
| 3. Training data | Earlier months of logs, dedup, decontamination against the test set, and an ablation of raw versus audited labels | dataset + dataset card |
| 4. Fine-tune | LoRA on 2 small models at 500 / 2,000 / 8,000 examples, all scored on the same frozen test set | learning curve with intervals |
| 5. Own vs rent | Cost per 1,000 tasks for: Claude (Sonnet and Haiku, with batch and caching prices), a hosted open model, a self-hosted GPU with idle time, and the fine-tuned model. Break-even volume, engineering time and a sensitivity chart | `report/` |
| 6. Ship | Public repo, Hugging Face dataset and adapters, static report page, portfolio deck draft, résumé bullets | when Samyak says publish |

## Train/test split

We split by time. Training uses complaints from earlier months and the test set uses later months. This copies real life, where you train on the past and run on the future. It also stops near-identical complaints from the same week from landing on both sides. Exact and near-duplicate checks run on top, and the kit refuses to score if any test item leaks into training.

## Keeping Claude usage inside the subscription

- Several complaints per `claude -p` call, to cut per-call overhead.
- Haiku for bulk work. Sonnet only where we measure that it matters.
- Token counts come from the JSON output of `claude -p`, so the cost model uses measured tokens multiplied by public list prices.

## Known risks

- Subscription limits cap how many Claude calls we can make, so samples stay in the hundreds. Intervals will be wide, and we will say so.
- A model trained on consumer labels may learn consumers' labeling habits, mistakes included. That's why we keep the two test views.
- Taxonomy drift: CFPB changed its product categories over the years (Apr 2017, Aug 2023, Oct 2026). We stick to one period with stable labels: complaints received from Aug 24, 2023 onward.
- CFPB stopped publishing narratives on Aug 14, 2026 (see `docs/phase0/dataset.md`). The live API no longer returns them, so the text comes from CFPB's public Narratives Archive (monthly ZIPs). The data window therefore ends Aug 14, 2026. Until we know why CFPB stopped, the plan is to avoid re-hosting complaint text. We share complaint IDs, our labels and a script that downloads the text from CFPB, along with the adapters.
- Free GPUs are slow and older (T4), so the latency we measure there won't match production GPUs. We'll use published benchmarks for those, cite them, and keep them separate from our own measurements.
- At list prices, Haiku may beat self-hosting on cost at most volumes. If that's the answer, we publish it.
