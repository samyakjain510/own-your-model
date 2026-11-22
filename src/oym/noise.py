"""Model-free label-noise check using exact duplicate texts.

If the same complaint text (after normalizing case and punctuation) was filed
more than once and got different labels, the text alone can't decide the label.
That gives two numbers per label field, measured without any model:

- pairwise agreement: pick two copies of the same text at random; how often do
  their labels match?
- majority ceiling: if a model always gave each text its most common label,
  what share of the duplicated items would it get right? No text-only model can
  beat this on these items.

These numbers only describe duplicated texts (mostly template letters), which
may be noisier or cleaner than unique complaints. We say so wherever we use them.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

from .leakage import exact_hash


def duplicate_label_agreement(corpus: str | Path, date_from: str, date_to: str, min_copies: int = 2) -> dict:
    groups: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    n_items = 0
    with open(corpus, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            d = r["Date received"][:10]
            if not (date_from <= d <= date_to):
                continue
            n_items += 1
            groups[exact_hash(r["Consumer complaint narrative"])].append((r["Product"], r["Issue"]))

    def summarize(clusters):
        pairs_same = {"product": 0, "pair": 0}
        pairs_total = 0
        majority = {"product": 0, "pair": 0}
        items = 0
        for labs in clusters:
            n = len(labs)
            items += n
            pairs_total += n * (n - 1)
            for field, key in (("product", lambda x: x[0]), ("pair", lambda x: x)):
                c = collections.Counter(key(x) for x in labs)
                pairs_same[field] += sum(v * (v - 1) for v in c.values())
                majority[field] += max(c.values())
        if not items:
            return None
        return {
            "clusters": len(clusters),
            "items_in_clusters": items,
            "pairwise_agreement_product": round(pairs_same["product"] / pairs_total, 3),
            "pairwise_agreement_product_issue": round(pairs_same["pair"] / pairs_total, 3),
            "majority_ceiling_product": round(majority["product"] / items, 3),
            "majority_ceiling_product_issue": round(majority["pair"] / items, 3),
        }

    dup_clusters = [labs for labs in groups.values() if len(labs) >= min_copies]
    by_majority_product = collections.defaultdict(list)
    for labs in dup_clusters:
        top = collections.Counter(x[0] for x in labs).most_common(1)[0][0]
        by_majority_product[top].append(labs)

    return {
        "window": [date_from, date_to],
        "items_scanned": n_items,
        "unique_texts": len(groups),
        "share_of_items_that_are_copies": round(sum(len(l) for l in dup_clusters) / n_items, 3) if n_items else None,
        "all_duplicate_clusters": summarize(dup_clusters),
        "by_majority_product": {p: summarize(c) for p, c in sorted(by_majority_product.items(), key=lambda x: -len(x[1]))},
    }
