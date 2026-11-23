# Lesson 9: the final test

## What "final" means here

Before opening the test set, I wrote down every choice: which models, which prompts, which scores, and which comparison is the main one (`docs/phase4/locked-choices.md`, committed first). Then every model answered the same 800 sealed test complaints, filed April to August 2026. Nothing was tuned after that.

The main comparison: the small model trained on 8,000 examples against Claude Haiku, on product-and-issue accuracy, against the consumers' own labels.

## Scores on the 800 test complaints

| Model | Product | Product and issue |
|---|---|---|
| Qwen3-4B, no training | 0.752 [0.721, 0.781] | 0.204 [0.177, 0.233] |
| Qwen3-4B trained on 500 | 0.743 [0.711, 0.772] | 0.287 [0.257, 0.320] |
| Qwen3-4B trained on 2,000 | 0.787 [0.758, 0.814] | 0.434 [0.400, 0.468] |
| **Qwen3-4B trained on 8,000** | **0.835 [0.808, 0.859]** | **0.514 [0.479, 0.548]** |
| Claude Haiku 5.5 | 0.810 [0.781, 0.836] | 0.424 [0.390, 0.458] |
| Claude Sonnet 5.5 | 0.854 [0.828, 0.877] | 0.489 [0.454, 0.523] |

## The main result

Same 800 complaints, gap between the 8,000-example model and Haiku:

| View | Product | Product and issue |
|---|---|---|
| Consumers' labels (main) | +2.5 (+0.2 to +5.0) | **+9.0 (+5.6 to +12.5)** |
| Only labels the checker accepted | +1.6 (−1.0 to +4.1) | +9.4 (+5.3 to +14.0) |
| Consumer's or checker's label counts | +1.3 (−1.1 to +3.8) | +6.9 (+3.0 to +11.0) |

The small model routes to the right issue about 9 points more often than Haiku, and that holds in every view. On product alone, it's slightly ahead against the consumers' labels and level in the other two views.

Against Sonnet, a much bigger rented model, it's level: −1.9 points on product (−4.1 to +0.4) and +2.5 on product and issue (−0.7 to +5.6). On product, Sonnet is about 3 points ahead when only the labels the checker accepted count.

## Dev vs test

Every model scored a few points lower on test than on dev. The 8,000-example model went from 0.540 to 0.514 on product and issue, and Haiku from 0.463 to 0.424 on its 300 dev complaints. The order stayed the same. Test complaints come from later months, so some drift is expected.

## What it costs

Per 1,000 complaints, from tokens measured on this test run:

| Option | Cost per 1,000 |
|---|---|
| Rent Haiku, batch | $0.080 |
| Rent Sonnet, batch | $0.960 |
| Own T4 GPU, kept busy | $0.102 |
| Trained model on a per-token host (stand-in price) | $0.042 |

Break-even, counting $2,833 a month of people time (an assumption):

| Instead of renting... | Own T4 | Per-token host |
|---|---|---|
| Haiku | never, at the measured speed | about 75 million a month |
| Sonnet | about 3.5 million a month | about 3.1 million a month |

Without the people cost, owning a T4 beats Sonnet from about 400,000 complaints a month, and still never beats Haiku.

## The answer

For routing consumer-finance complaints, a 4-billion-parameter open model trained on 8,000 logged examples:

- **beats Claude Haiku by 9 points** on routing to the right issue,
- **matches Claude Sonnet**,
- **costs about a tenth of Sonnet per complaint** on a single rented T4 GPU, and a little more than Haiku.

So owning pays off when you need better than Haiku's quality and your volume is in the low millions a month or more. If Haiku's quality is good enough, rent Haiku: at about $80 per million complaints, it's very hard to beat on price.

## What went wrong in the final run

Seven complaints (0.9%) were so long that cutting the prompt to fit also cut off the "now answer" cue at its end, so the trained models kept writing the complaint instead of answering. Under the locked rules those count as wrong, so the small model's real score may be up to 0.9 points higher. It's fixed in the kit now (`what-went-wrong.md`, item 13).

## Limits

- One task, one dataset, one small model. Other jobs may come out differently.
- "Right" means agreeing with the consumer's own pick, which is noisy. The checker views help, but nobody checked labels by hand.
- The per-token host price is a stand-in (a hosted 9B open model). I haven't confirmed a host serves this adapter at that price.
- Speed was measured on a T4 only. Newer GPUs would likely be faster, but I haven't measured them.
- The people cost is an assumption, and it moves every break-even point.

Where the numbers come from: `runs/final/summary.json`, `runs/final/cost_test.json`, `runs/final/main_vs_sonnet.json`, built by `scripts/final_report.py`.
