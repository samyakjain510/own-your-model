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
| Qwen3-4B trained on 8,000 examples | 800 | 0.833 [0.805, 0.857] | 0.540 [0.505, 0.574] |
| Claude Haiku 5.5, given the label list | 300 | 0.827 [0.780, 0.865] | 0.463 [0.408, 0.520] |
| Claude Haiku 5.5, same, low effort (little thinking) | 300 | 0.783 [0.733, 0.826] | 0.340 [0.289, 0.395] |

The brackets are 95% intervals: the range the true score probably sits in, given how many complaints we checked.

## Head to head on the same 300 complaints

Haiku only answered the first 300 dev complaints, to save my subscription's usage. So the fair comparison uses just those 300. For each complaint I note which model got it right, then resample the complaints 2,000 times to see how much the gap moves around.

| Small model vs Haiku (default effort) | Product gap | Product-and-issue gap |
|---|---|---|
| Trained on 2,000 | −1.7 points (−5.3 to +2.0) | +3.7 points (−2.0 to +9.3) |
| Trained on 8,000 | +1.7 points (−1.3 to +5.3) | +10.7 points (+5.3 to +16.0) |

At 2,000 examples, both intervals include zero, so I can't tell the two apart. At 8,000 examples, the small model is ahead on the harder score by about 11 points, and the whole interval sits above zero. On product alone they're still level.

The 8,000-example model took 3 hours to train on Kaggle's free T4 GPU. Its validation loss was still falling at the last checkpoint, so more data or another pass might help further. I haven't tried that.

## Four things I noticed

**Training mostly helps with the issue.** From no training to 8,000 examples, the product score rose 9 points and the product-and-issue score went from 0.22 to 0.54. My guess is that consumers have habits in how they pick an issue from the form's list, and the trained model has seen thousands of those choices. Claude has to guess them. That's a hypothesis I haven't tested yet.

**Training fixed made-up label combinations.** With no training, the small model paired a product with an issue that doesn't belong to it 74 times out of 800. After training on 2,000 or 8,000 examples, it did that twice.

**The trained model reads a fifth as much.** Without training, every prompt has to carry the full label list: 1,863 tokens per complaint on average. The trained model has learned the labels, so its prompt is just the company and the complaint: 381 tokens. Fewer tokens means a cheaper and faster answer, and lesson 7 turns that into dollars.

**Haiku's thinking is worth paying for.** By default Haiku thought before answering on 23 of 30 calls. At low effort it thought much less (25 thinking tokens per complaint instead of 138) and wrote 40% as many output tokens, but its product-and-issue score fell 12 points (interval 8 to 17). So the fair "rent" price is the one with thinking.

## What these results don't show yet

- These are dev numbers. I looked at dev errors while building, so they may flatter me a little. The sealed test set decides the final scores.
- Haiku got the label list and no worked examples. A prompt with a few examples might close the gap. I haven't tried that yet.
- The scores count agreement with the consumer's pick. A label checker that flags clearly wrong consumer labels is being tested, so I can also report scores without those.

Where the numbers come from: `runs/kaggle/oym-qwen3-4b-*/results/*/score.json`, `runs/dev-haiku55-route-v2*/score.json` and `runs/compare/*.json`.
