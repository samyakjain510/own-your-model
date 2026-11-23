# Lesson 8: own or rent, in dollars

## The question

A company routes complaints every month. It can rent Claude and pay per complaint, or own a small trained model and pay for the machine it runs on. Which costs less, and at what volume does the answer flip?

## The options

All prices are per 1,000 complaints, built from the tokens and speeds we measured plus published prices (`configs/cost_inputs.json` lists each source).

| Option | Cost per 1,000 | How it's built |
|---|---|---|
| Rent Claude Haiku, batch pricing | $0.084 | Measured tokens, including thinking, at list price with the 50% batch discount |
| Rent Claude Haiku, low effort, batch | $0.053 | Same, with less thinking. It scores 12 points lower on product and issue |
| Rent an untrained open model per token | $0.190 | It needs the long label list in every prompt: 1,863 tokens |
| Own the trained model on one T4 GPU, kept busy | $0.102 | $0.526 an hour, 2.40 complaints a second, busy 60% of the time |
| Trained model on a per-token host | $0.041 | Short prompt (381 tokens), at a 9B open model's hosted price |

Two surprises:

1. **Haiku is very cheap for this job.** About $84 for a million complaints.
2. **Owning a GPU costs more per complaint than renting Haiku, even before paying anyone to run it.** One T4 answered 2.40 complaints a second. To match Haiku it would need 2.91.

## The costs that don't shrink with volume

**The GPU bills by the hour, busy or idle.** One T4 for a month is $384, whether it handles ten complaints or two million.

**People.** Someone has to build the pipeline, retrain when the labels change, and keep the server up. I assumed 10 days to build, spread over a year, plus 2 days a month of upkeep, at $1,000 a day. That's $2,833 a month. It's an assumption, and it's the biggest number in the model, so the break-even points below are shown with and without it.

## Monthly bill at different volumes

| Complaints per month | Haiku, batch | Own T4 + people | Per-token host + people |
|---|---|---|---|
| 100,000 | $8 | $3,217 (1 GPU) | $2,837 |
| 1,000,000 | $84 | $3,217 (1 GPU) | $2,875 |
| 10,000,000 | $837 | $3,985 (3 GPUs) | $3,246 |
| 100,000,000 | $8,373 | $13,201 (27 GPUs) | $6,956 |

Break-even against Haiku with batch pricing:
- **Own T4:** never, at the measured speed, with or without the people cost.
- **Per-token host, counting people:** about 68 million complaints a month.
- **Per-token host, leaving people out:** cheaper from the first complaint.

## Where owning does win: quality

On the same 300 dev complaints, the model trained on 8,000 examples got product and issue right 57% of the time and Haiku 46%. That gap held when doubtful labels were set aside (lesson 7).

Counted per correct answer, the own T4 and Haiku come out about even: $0.178 vs $0.181 per 1,000 complaints routed fully right. So the honest summary for this job is:

- **If the cheapest routing is the goal, rent Haiku.** Owning only pays on cost at tens of millions of complaints a month, and only on a per-token host.
- **If routing to the right issue matters,** for example because a wrong issue sends the complaint to the wrong team, owning buys about 11 more points for a similar or higher bill. Whether that's worth $3,000 a month in people time depends on what a misrouted complaint costs, which the kit can't know.

## What could change the answer

- **Speed.** The T4 is 21% short of matching Haiku. vLLM, the usual serving software, was slower here (2.02 a second) because the T4 is too old for its fast paths. A newer GPU (L4) costs $0.69 an hour and would need 3.82 a second to match. I haven't measured an L4.
- **The per-token host price is a stand-in.** It uses a hosted 9B open model's price. I haven't confirmed that a host serves our trained 4B adapter at that price.
- **These are dev numbers.** The sealed test set gives the final scores.
- **Claude's prices.** A price cut on Haiku pushes every break-even further out.

Where the numbers come from: `runs/cost/report_v1_dev.json`, built by `src/oym/cost.py` from `runs/dev-haiku55-route-v2*`, `runs/kaggle/oym-qwen3-4b-b/results/qwen3-4b-n8000/result.json` and `runs/kaggle/oym-bench-hf-qwen3-4b-n8000/bench/hf_generate.json`.
