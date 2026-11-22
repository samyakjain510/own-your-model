"""Score a run's predictions against the logged labels (the "as logged" view).

All checks here are plain code: exact match on product, and on product plus
issue. A missing answer counts as wrong. An issue that doesn't belong to the
predicted product counts as invalid and wrong.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

from .metrics import wilson


def score(run_dir: str | Path, labels_path: str | Path) -> dict:
    run_dir = Path(run_dir)
    labels = json.loads(Path(labels_path).read_text())
    rows = [json.loads(line) for line in open(run_dir / "predictions.jsonl")]
    n = len(rows)
    prod_ok = pair_ok = missing = invalid = 0
    per_product = collections.defaultdict(lambda: [0, 0])  # gold product -> [correct product, total]
    confusions = collections.Counter()
    for r in rows:
        g, p = r["gold"], r["pred"]
        per_product[g["product"]][1] += 1
        if not p:
            missing += 1
            continue
        if p["issue"] not in labels.get(p["product"], []):
            invalid += 1
        if p["product"] == g["product"]:
            prod_ok += 1
            per_product[g["product"]][0] += 1
            if p["issue"] == g["issue"]:
                pair_ok += 1
        else:
            confusions[(g["product"], p["product"])] += 1

    per_prod_rates = {k: wilson(v[0], v[1]) for k, v in per_product.items()}
    macro = sum(r.p for r in per_prod_rates.values()) / len(per_prod_rates)
    calls = [json.loads(line) for line in open(run_dir / "calls.jsonl")] if (run_dir / "calls.jsonl").exists() else []
    tok_in = sum(c["usage"].get("input_tokens", 0) + c["usage"].get("cache_read_input_tokens", 0)
                 + c["usage"].get("cache_creation_input_tokens", 0) for c in calls)
    tok_out = sum(c["usage"].get("output_tokens", 0) for c in calls)
    result = {
        "n": n,
        "product_accuracy": str(wilson(prod_ok, n)),
        "product_and_issue_accuracy": str(wilson(pair_ok, n)),
        "product_macro_avg": round(macro, 3),
        "missing_answers": missing,
        "invalid_issue_for_product": invalid,
        "per_product": {k: str(v) for k, v in sorted(per_prod_rates.items(), key=lambda x: -x[1].n)},
        "top_product_confusions (gold -> pred)": [f"{g} -> {p}: {c}" for (g, p), c in confusions.most_common(8)],
        "tokens_per_item": {"input": round(tok_in / n, 1) if n else None, "output": round(tok_out / n, 1) if n else None},
        "cost_usd_equiv_total": round(sum(c.get("cost_usd_equiv") or 0 for c in calls), 4),
    }
    (run_dir / "score.json").write_text(json.dumps(result, indent=2))
    return result
