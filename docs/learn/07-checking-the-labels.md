# Lesson 7: checking the labels themselves

## The problem

Every score so far asks: did the model pick the same label as the consumer? But consumers pick their own labels on the CFPB form, and some pick wrong. A model that reads the complaint correctly can still lose points for disagreeing with a mistake.

Nobody is hand-labeling here, so I can't hire people to fix the labels. What I can do is have a strong model read each complaint next to its logged label and say whether the label fits. I call it the label checker.

## Two rules for the checker

1. **It's never one of the contestants.** The checker is Claude Opus 5.5. The models being compared are Qwen3-4B and Claude Haiku. No model grades itself.
2. **It only sees the logged label.** It never sees any model's answer, so it can't favor one.

## Testing the checker before trusting it

A checker is only useful if it catches wrong labels without flagging everything. To test it, I took 400 dev complaints and secretly swapped in a wrong label on about half of them:

- **Wrong product** (84 complaints): usually a product the models often confuse with the real one, so these are hard swaps.
- **Wrong issue** (97 complaints): same product, different issue.
- **Left alone** (219 complaints): the consumer's own label.

Then the checker reviewed all 400, without knowing which were swapped.

| What I planted | Checker flagged it | 95% interval |
|---|---|---|
| Wrong product | 96% | 90% to 99% |
| Wrong issue | 86% | 77% to 91% |
| Nothing (consumer's own label) | 22% | 17% to 28% |

When it caught a wrong product, it named the original product 88% of the time.

## How to read the 22%

The checker disagreed with 1 in 10 of the consumers' products and 1 in 8 of their issues. Some of those are real consumer mistakes: complaints filed against a credit bureau but labeled Debt collection, or a Cash App complaint labeled Credit card. Some are judgment calls, like a bank collecting its own debt. I can't tell what share is which without people checking them, so the 22% is a ceiling on the checker's false alarms, not a measurement of them.

So I don't replace the logged labels with the checker's. I report scores both ways: against the logged labels, and against only the complaints whose label the checker accepted. If a model wins both ways, the label noise isn't what's deciding the result.

## What happened on the 300 complaints both models answered

The checker accepted 252 of the 300 logged labels. It called 23 the wrong product and 25 the wrong issue.

Product-and-issue scores three ways:

| Model | Logged labels (300) | Only labels the checker accepted (252) | Logged or checker's label counts (300) |
|---|---|---|---|
| Qwen3-4B trained on 8,000 | 0.570 | 0.659 | 0.637 |
| Qwen3-4B trained on 2,000 | 0.500 | 0.575 | 0.570 |
| Claude Haiku 5.5 | 0.463 | 0.552 | 0.553 |
| Claude Haiku 5.5, low effort | 0.340 | 0.401 | 0.417 |
| Qwen3-4B, no training | 0.253 | 0.298 | 0.293 |

Every model scores higher once doubtful labels are set aside, by 5 to 9 points. The order doesn't change.

The head-to-head gap between the 8,000-example model and Haiku, with 95% intervals:

| View | Product | Product and issue |
|---|---|---|
| Logged labels | +1.7 (−1.3 to +5.3) | +10.7 (+5.3 to +16.0) |
| Only labels the checker accepted | +1.8 (−1.4 to +5.4) | +10.7 (+4.4 to +17.1) |
| Logged or checker's label counts | +1.7 (−1.3 to +5.3) | +8.3 (+2.3 to +14.7) |

The small model's lead on the harder score holds in every view, and the two are level on product in every view.

## One thing to watch

The checker and Haiku are both Claude models. If they share a view of what a label means, the checker's version could tilt toward Haiku. There's a small sign of that: when the checker's suggested label also counts as right, Haiku gains 9 points and the 8,000-example model gains 7, so the gap narrows from 10.7 to 8.3. It doesn't close.

Where the numbers come from: `runs/audit-calib-opus55-n400/score.json`, `runs/audit-dev300-opus55/`, `runs/compare/dev300_audited*.json`; code in `src/oym/audit.py`.
