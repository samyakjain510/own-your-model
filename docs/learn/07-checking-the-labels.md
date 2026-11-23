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

## One thing to watch

The checker and Haiku are both Claude models. If they share a view of what a label means, the checker's version could tilt toward Haiku. I'll check that by seeing how much each model's score moves when the flagged complaints are dropped.

Where the numbers come from: `runs/audit-calib-opus55-n400/score.json` and `verdicts.jsonl`; code in `src/oym/audit.py`.
