"""Label checker ("auditor"): a Claude model reads a complaint and its logged label and says whether the label fits.

Why: consumers pick the labels, and some pick wrong. Scoring only against logged labels
punishes a model for disagreeing with a mistake. The checker lets us also report an
"audited" score that leaves out labels it judges clearly wrong.

Before trusting it, we test it: take dev complaints, swap in a wrong label on about half
(planted errors), and measure how often it catches a planted error (true positive rate)
and how often it flags an untouched logged label (flag rate on logged labels, which
includes real consumer mistakes, so it isn't a pure false-alarm rate).

Rules: the checker model is never one of the models being compared (no model grades
itself), and it never sees any model's answers, only the logged label.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import claude_cli
from .baseline import company_of, truncate
from .metrics import wilson
from .schema import read_traces
from .split import MAX_WORDS, verify_frozen

VERDICTS = ["fits", "wrong_product", "wrong_issue"]


def judge_system(labels: dict[str, list[str]]) -> str:
    lines = [
        "You check labels on consumer complaints filed with the US Consumer Financial Protection Bureau. "
        "Each complaint shows the company it was filed against, the complaint text, and the product and issue "
        "the consumer picked on the form.",
        "",
        "Decide for each one:",
        '- "fits": the label is a reasonable reading of the complaint. Issues often overlap, and consumers pick '
        "among several reasonable options. If the picked label is one of them, it fits.",
        '- "wrong_product": the product clearly doesn\'t match the kind of account or service the consumer has '
        "with that company. A complaint against a debt collector is Debt collection even if it mentions a credit "
        "report; a complaint against a credit reporting company is about credit reporting.",
        '- "wrong_issue": the product fits, but the issue clearly doesn\'t match what the complaint is mainly about.',
        "",
        "Only flag a label when it is clearly wrong. When you flag one, also give the label you think fits best. "
        "When it fits, repeat the picked label. Text like [REDACTED] marks details removed for privacy.",
        "",
        "Allowed products and their issues:",
    ]
    for product in sorted(labels):
        lines.append(f"\nPRODUCT: {product}")
        lines += [f"  - {issue}" for issue in labels[product]]
    lines.append("\nReturn one answer per complaint, using the complaint's id.")
    return "\n".join(lines)


def judge_schema(labels: dict[str, list[str]]) -> dict:
    issues = sorted({i for v in labels.values() for i in v})
    item = {"type": "object", "properties": {
        "id": {"type": "string"}, "verdict": {"type": "string", "enum": VERDICTS},
        "product": {"type": "string", "enum": sorted(labels)}, "issue": {"type": "string", "enum": issues}},
        "required": ["id", "verdict", "product", "issue"], "additionalProperties": False}
    return {"type": "object", "properties": {"answers": {"type": "array", "items": item}},
            "required": ["answers"], "additionalProperties": False}


def judge_prompt(items: list[tuple]) -> str:
    """items: (trace, shown_label)."""
    parts = [f"Check these {len(items)} labels.\n"]
    for t, lab in items:
        parts.append(f'<complaint id="{t.trace_id}" company="{company_of(t)}">\n{truncate(t.input)}\n</complaint>\n'
                     f'<picked_label product="{lab["product"]}" issue="{lab["issue"]}"/>\n')
    return "\n".join(parts)


def _judge(items, labels, run_dir, model, batch_size, workers, effort):
    system, schema = judge_system(labels), judge_schema(labels)
    batches = [items[k : k + batch_size] for k in range(0, len(items), batch_size)]

    def one(bi_batch):
        bi, batch = bi_batch
        t0 = time.time()
        r = claude_cli.call(judge_prompt(batch), system=system, model=model, schema=schema, effort=effort)
        return bi, batch, r, time.time() - t0

    verdicts, calls = {}, []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for bi, batch, r, dt in pool.map(one, enumerate(batches)):
            ids = {t.trace_id for t, _ in batch}
            for a in (r.data.get("answers", []) if isinstance(r.data, dict) else []):
                if a.get("id") in ids:
                    verdicts[a["id"]] = {k: a.get(k) for k in ("verdict", "product", "issue")}
            calls.append({"batch": bi, "n": len(batch), "n_answered": sum(1 for t, _ in batch if t.trace_id in verdicts),
                          "usage": r.usage, "cost_usd_equiv": r.cost_usd_equiv, "models_used": r.models_used,
                          "cached": r.cached, "seconds": round(dt, 2)})
            print(f"batch {bi + 1}/{len(batches)}: {calls[-1]['n_answered']}/{len(batch)}"
                  f"{' (cached)' if r.cached else f' in {dt:.0f}s'}", flush=True)
    with open(run_dir / "calls.jsonl", "w") as f:
        for c in calls:
            f.write(json.dumps(c) + "\n")
    (run_dir / "system_prompt.txt").write_text(system)
    return verdicts, hashlib.sha256(system.encode()).hexdigest()


def plant_errors(traces, labels, seed: int, confusable: dict[str, list[str]] | None = None):
    """Swap in a wrong label on about half the items. Half the swaps change the product
    (to an often-confused product when we know one), half change only the issue."""
    rng = random.Random(seed)
    products = sorted(labels)
    out = []
    for t in traces:
        gold = {"product": t.output["product"], "issue": t.output["issue"]}
        kind = rng.choice(["none", "none", "product", "issue"])
        if kind == "issue" and len(labels.get(gold["product"], [])) < 2:
            kind = "product"
        if kind == "none":
            shown = gold
        elif kind == "product":
            pool = [p for p in (confusable or {}).get(gold["product"], []) if p != gold["product"]]
            p = rng.choice(pool) if pool and rng.random() < 0.7 else rng.choice([x for x in products if x != gold["product"]])
            shown = {"product": p, "issue": rng.choice(labels[p])}
        else:
            shown = {"product": gold["product"], "issue": rng.choice([i for i in labels[gold["product"]] if i != gold["issue"]])}
        out.append((t, shown, kind, gold))
    return out


def calibrate(eval_dir, run_dir, *, model: str, version: str = "v1", start: int = 300, n: int = 200,
              seed: int = 11, batch_size: int = 10, workers: int = 4, effort: str | None = None,
              confusable: dict | None = None) -> dict:
    eval_dir, run_dir = Path(eval_dir), Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = verify_frozen(eval_dir, version, name="dev")
    labels = json.loads((eval_dir / f"labels_{version}.json").read_text())
    traces = list(read_traces(path))[start : start + n]
    planted = plant_errors(traces, labels, seed, confusable)
    verdicts, sys_hash = _judge([(t, shown) for t, shown, _, _ in planted], labels, run_dir, model,
                                batch_size, workers, effort)
    rows, by_kind = [], {"none": [0, 0], "product": [0, 0], "issue": [0, 0]}
    recovered = [0, 0]
    for t, shown, kind, gold in planted:
        v = verdicts.get(t.trace_id)
        flagged = bool(v) and v["verdict"] != "fits"
        by_kind[kind][0] += flagged
        by_kind[kind][1] += 1
        if kind == "product" and flagged:
            recovered[1] += 1
            recovered[0] += v["product"] == gold["product"]
        rows.append({"trace_id": t.trace_id, "planted": kind, "shown": shown, "gold": gold, "verdict": v})
    with open(run_dir / "verdicts.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    result = {
        "kind": "auditor_calibration", "model": model, "effort": effort or "CLI default", "split": "dev",
        "slice": [start, start + len(traces)], "seed": seed, "batch_size": batch_size, "max_words": MAX_WORDS,
        "system_prompt_sha256": sys_hash, "missing_verdicts": sum(1 for r in rows if not r["verdict"]),
        "catches_planted_wrong_product": str(wilson(*by_kind["product"])),
        "catches_planted_wrong_issue": str(wilson(*by_kind["issue"])),
        "flags_untouched_logged_labels": str(wilson(*by_kind["none"])),
        "suggests_original_product_when_catching_product_swap": str(wilson(*recovered)) if recovered[1] else None,
        "note": "Untouched labels include real consumer mistakes, so their flag rate is an upper bound on false alarms.",
    }
    (run_dir / "score.json").write_text(json.dumps(result, indent=2))
    return result


def audit_split(eval_dir, run_dir, *, model: str, split: str, version: str, start: int = 0,
                limit: int | None = None, batch_size: int = 10, workers: int = 4, effort: str | None = None) -> dict:
    """Run the checker on the logged labels of a frozen split (nothing planted)."""
    eval_dir, run_dir = Path(eval_dir), Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = verify_frozen(eval_dir, version, name=split)
    labels = json.loads((eval_dir / f"labels_{version}.json").read_text())
    traces = list(read_traces(path))[start : (start + limit) if limit else None]
    items = [(t, {"product": t.output["product"], "issue": t.output["issue"]}) for t in traces]
    verdicts, sys_hash = _judge(items, labels, run_dir, model, batch_size, workers, effort)
    with open(run_dir / "verdicts.jsonl", "w") as f:
        for t, lab in items:
            f.write(json.dumps({"trace_id": t.trace_id, "logged": lab, "verdict": verdicts.get(t.trace_id)}) + "\n")
    counts = {v: sum(1 for x in verdicts.values() if x["verdict"] == v) for v in VERDICTS}
    config = {"kind": "auditor_run", "model": model, "effort": effort or "CLI default", "split": split,
              "version": version, "slice": [start, start + len(traces)], "batch_size": batch_size,
              "system_prompt_sha256": sys_hash, "verdict_counts": counts,
              "missing_verdicts": len(traces) - len(verdicts)}
    (run_dir / "config.json").write_text(json.dumps(config, indent=2))
    return config


def audited_scores(pred_dir, audit_dir) -> dict:
    """Score a run two extra ways using the checker's verdicts on the logged labels:
    - kept: only complaints whose logged label the checker accepted ("fits").
      For product accuracy, complaints flagged only for the issue are kept.
    - either: a prediction counts as right if it matches the logged label OR the checker's suggestion.
    """
    verdicts = {json.loads(l)["trace_id"]: json.loads(l) for l in open(Path(audit_dir) / "verdicts.jsonl")}
    preds = [json.loads(l) for l in open(Path(pred_dir) / "predictions.jsonl")]
    preds = [p for p in preds if p["trace_id"] in verdicts and verdicts[p["trace_id"]]["verdict"]]
    out = {"pred_run": str(pred_dir), "audit_run": str(audit_dir), "n": len(preds)}
    for level in ("product", "product_and_issue"):
        kept_ok = kept_n = either_ok = 0
        for p in preds:
            v = verdicts[p["trace_id"]]["verdict"]
            g, pr = p["gold"], p["pred"] or {}

            def match(lab):
                return pr.get("product") == lab["product"] and (level == "product" or pr.get("issue") == lab["issue"])

            keep = v["verdict"] == "fits" or (level == "product" and v["verdict"] == "wrong_issue")
            if keep:
                kept_n += 1
                kept_ok += match(g)
            either_ok += match(g) or (v["verdict"] != "fits" and match(v))
        out[level] = {"as_logged": str(wilson(sum(1 for p in preds if p["pred"] and (
                          p["pred"].get("product") == p["gold"]["product"] and (level == "product" or
                          p["pred"].get("issue") == p["gold"]["issue"]))), len(preds))),
                      "kept_only": str(wilson(kept_ok, kept_n)),
                      "logged_or_checker": str(wilson(either_ok, len(preds)))}
    return out
