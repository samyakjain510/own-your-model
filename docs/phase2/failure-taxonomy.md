# Failure taxonomy, draft 1

**Who made this:** Claude (lead agent) open-coded every product-level miss from the 100-complaint pilot (`runs/pilot-haiku55-n100`, Haiku 5.5, prompt route-v1), then grouped them. No human labeled or reviewed these codes. Counts are from that pilot (24 product misses) and are rough, since one person-equivalent (an AI) did the coding.

| Code | What it looks like | Pilot misses | Fix tried | Effect on dev (n=300) |
|---|---|---|---|---|
| **Two products in one complaint** | A debt (collection, card, car loan) shows up on a credit report. The consumer filed by the company they're angry at; the model routed by topic. | ~11 | route-v2: show the company name and state the routing rule | Debt collection → Credit reporting fell from 22 to 9 |
| **Fuzzy line for app-based money services** | Cash App, Chime and similar: checking vs. money transfer vs. prepaid card. Consumers pick differently for the same kind of problem. | ~7 | none yet | Checking → Money transfer: 8 → 5 |
| **Card type unclear** | A card dispute where the text doesn't say debit or credit. | ~3 | none yet | n/a |
| **Likely consumer mislabel** | The logged label looks wrong on reading (a Chime debit-card complaint filed as Credit card). | ~1–2 | goes to the "audited" test view, not to prompt changes | n/a |
| **Clear model error** | The model misread the text (Affirm flight financing called a vehicle loan). | ~2–3 | none | n/a |
| **Outdated label name** | Without a label list, the model used a category retired in Aug 2023. | seen once in an early test | label list in prompt + schema that only accepts allowed labels | gone (0 invalid labels) |

## Not coded yet

- **Issue-level misses.** Product+issue accuracy is ~43–46% on dev, so most errors are at the issue level. These need the same open-coding pass. The early hypothesis is that many issue pairs overlap (for example "Attempts to collect debt not owed" vs. "False statements or representation"), so consumers pick inconsistently. That hypothesis is untested.
