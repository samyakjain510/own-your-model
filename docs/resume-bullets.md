# Résumé bullets (measured numbers only)

- Built an open-source pipeline that turns raw workflow logs into a leak-checked eval set and training data; a 4B open model fine-tuned on 8,000 logged examples routed consumer-finance complaints to the exact product and issue 9 points more often than Claude Haiku (51.4% vs 42.4% on 800 sealed test cases) and matched Claude Sonnet, using $0 of paid compute.
- Built an own-vs-rent cost model from measured tokens and GPU throughput: self-hosting on one T4 cost $0.10 per 1,000 tasks vs $0.96 for Sonnet, breaking even at about 3.5M tasks a month including people time, and never beating Haiku on price.

Sources: `runs/final/summary.json`, `runs/final/cost_test.json`. The people cost ($2,833 a month) is an assumption, stated in `configs/cost_inputs.json`.
