# Lesson 6: first results, small model vs Claude

## What I compared

Every model answered the same dev complaints and was graded by the same code. Dev is the set I'm allowed to look at and tune on. The sealed test set comes last, once every choice is locked.

Two scores:
- **Product**: did it pick the right one of the 11 products?
- **Product and issue**: did it also pick the right issue? There are 138 product-issue pairs, so this is much harder.

"Right" means it matches what the consumer picked on the CFPB form. Consumers make mistakes, so no model can reach 100%.

## The numbers (dev set)

| Model | Complaints | Product | Product and issue |
|---|---|---|---|
| Qwen3-4B, no training, given the label list | 800 | 0.743 [0.711, 0.772] | 0.219 [0.191, 0.249] |
| Qwen3-4B trained on 500 examples | 800 | 0.757 [0.727, 0.786] | 0.329 [0.297, 0.362] |
| Qwen3-4B trained on 2,000 examples | 800 | 0.802 [0.773, 0.829] | 0.485 [0.451, 0.520] |
| Claude Haiku 5.5, given the label list | 300 | 0.827 [0.780, 0.865] | 0.463 [0.408, 0.520] |

The brackets are 95% intervals: the range the true score probably sits in, given how many complaints we checked.

## Head to head on the same 300 complaints

Haiku only answered the first 300 dev complaints, to save my subscription's usage. So the fair comparison uses just those 300. For each complaint I note which model got it right, then resample the complaints 2,000 times to see how much the gap moves around.

| Trained on 2,000 vs Haiku | Gap | 95% interval |
|---|---|---|
| Product | −1.7 points | −5.3 to +2.0 |
| Product and issue | +3.7 points | −2.0 to +9.3 |

Both intervals include zero. On this data I can't tell the two apart. A 4-billion-parameter model, trained for 45 minutes on a free GPU, is level with Claude Haiku on this job.

## Three things I noticed

**Training mostly helps with the issue.** The product score rose 6 points from no training to 2,000 examples. The product-and-issue score more than doubled. My guess is that consumers have habits in how they pick an issue from the form's list, and the trained model has seen thousands of those choices. Claude has to guess them. That's a hypothesis I haven't tested yet.

**Training fixed made-up label combinations.** With no training, the small model paired a product with an issue that doesn't belong to it 74 times out of 800. After training on 2,000 examples, it did that twice.

**The trained model reads a fifth as much.** Without training, every prompt has to carry the full label list: 1,863 tokens per complaint on average. The trained model has learned the labels, so its prompt is just the company and the complaint: 381 tokens. Fewer tokens means a cheaper and faster answer, and lesson 7 turns that into dollars.

## What these results don't show yet

- These are dev numbers. I looked at dev errors while building, so they may flatter me a little. The sealed test set decides the final scores.
- Haiku got the label list and no worked examples. A prompt with a few examples might close the gap. I haven't tried that yet.
- The 8,000-example run is still training.
- Speed: the plain setup answered 1.46 complaints a second on the free GPU. A speed test with production serving software (vLLM) is running.

Where the numbers come from: `runs/kaggle/oym-qwen3-4b-a/results/*/score.json` and `runs/compare/dev300_vs_haiku_v2.json`.
