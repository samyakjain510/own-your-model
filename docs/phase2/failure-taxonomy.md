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

- **Issue-level misses: counted, not yet read.** A code-only count of mix-ups where the product was right and the issue wrong (`dev`, no complaint text read):
  - Qwen3-4B trained on 8,000 (800 complaints): product wrong 16.4%, product right but issue wrong 29.2%. Haiku (300 complaints): 17.3% and 36.3%. So most misses for both models are at the issue level.
  - The biggest cluster is three Debt collection issues that both models swap in every direction: "Attempts to collect debt not owed", "False statements or representation" and "Written notification about debt" (48 of the small model's 234 issue misses). The next are Checking "Managing an account" vs. fee and investigation issues, and Money transfer "Fraud or scam" vs. "Unauthorized transactions".
  - That fits the overlap hypothesis: a letter demanding a debt the consumer says they don't owe can honestly be any of the three. Reading the texts to confirm it is still to do.
