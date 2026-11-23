"""Run a rented model (Claude, through the CLI) on the frozen test set.

Each call sends K complaints and asks for one product and one issue per
complaint, picked from the allowed list. The output is forced to a JSON
schema whose product and issue fields only accept allowed strings, so typos
are impossible. Picking an issue that doesn't belong to the chosen product
is still possible, and the scorer counts it as wrong.

Everything needed to reproduce a run is saved next to its predictions:
model, prompt hash, test-set hash, batch size, seed, and token usage per call.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import claude_cli
from .schema import read_traces
from .split import MAX_WORDS, verify_frozen

PROMPT_VERSIONS = ("route-v1", "route-v2", "route-v3")
# route-v1: complaint text only.
# route-v2: adds the company the complaint is filed against (it's on the intake form) and one
#           routing rule: the product is the kind of account the consumer has with that company.
# route-v3: route-v2 plus 22 worked examples (2 per product, short complaints) taken from the
#           TRAINING pool, never from dev or test. Gives Claude the same kind of hint the small
#           model gets from training, in a form a rented model can use.

EXAMPLES_PATH = Path(__file__).resolve().parents[2] / "data" / "train" / "train_8000.jsonl"


def worked_examples(labels: dict[str, list[str]], per_product: int = 2, seed: int = 0,
                    min_words: int = 40, max_words: int = 120) -> list[dict]:
    """Pick short training examples, per_product for each product, with different issues when possible."""
    rows = [json.loads(line) for line in open(EXAMPLES_PATH)]
    rng = random.Random(seed)
    rng.shuffle(rows)
    picked, seen = {p: [] for p in labels}, set()
    for r in rows:
        user, answer = r["messages"][1]["content"], json.loads(r["messages"][2]["content"])
        company, _, text = user.partition("\n\nComplaint:\n")
        p, i = answer["product"], answer["issue"]
        n = len(text.split())
        if p not in picked or len(picked[p]) >= per_product or (p, i) in seen or not (min_words <= n <= max_words):
            continue
        picked[p].append({"trace_id": r["trace_id"], "company": company.removeprefix("Company: "), "text": text,
                          "product": p, "issue": i})
        seen.add((p, i))
    return [e for p in sorted(picked) for e in picked[p]]


def truncate(text: str, max_words: int = MAX_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " [truncated]"


def system_prompt(labels: dict[str, list[str]], prompt_version: str = "route-v1") -> str:
    intro = ("You route consumer complaints about financial products, filed with the US Consumer Financial "
             "Protection Bureau. For each complaint, pick exactly one product and one issue from the list below. "
             "The issue must be one listed under the product you pick. Pick what the complaint is mainly about. "
             "Text like [REDACTED] marks details removed for privacy.")
    if prompt_version in ("route-v2", "route-v3"):
        intro += ("\n\nEach complaint shows the company it was filed against. The product is the kind of account "
                  "or service the consumer has with that company. For example, a complaint against a debt collector "
                  "or debt buyer is Debt collection even if it mentions a credit report, and a complaint against a "
                  "credit reporting company is about credit reporting.")
    lines = [
        intro,
        "",
        "Allowed products and their issues:",
    ]
    for product in sorted(labels):
        lines.append(f"\nPRODUCT: {product}")
        for issue in labels[product]:
            lines.append(f"  - {issue}")
    if prompt_version == "route-v3":
        lines.append("\nWorked examples (real complaints with the label the consumer picked):")
        for k, e in enumerate(worked_examples(labels), 1):
            lines.append(f'\n<example n="{k}" company="{e["company"]}">\n{e["text"]}\n</example>\n'
                         f'Answer: product="{e["product"]}", issue="{e["issue"]}"')
    lines.append("\nReturn one answer per complaint, using the complaint's id.")
    return "\n".join(lines)


def answer_schema(labels: dict[str, list[str]]) -> dict:
    issues = sorted({i for v in labels.values() for i in v})
    return {
        "type": "object",
        "properties": {
            "answers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "product": {"type": "string", "enum": sorted(labels)},
                        "issue": {"type": "string", "enum": issues},
                    },
                    "required": ["id", "product", "issue"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["answers"],
        "additionalProperties": False,
    }


def company_of(t) -> str:
    return t.context.get("company") or t.metadata.get("company") or "unknown"


def user_prompt(batch, prompt_version: str = "route-v1") -> str:
    parts = [f"Route these {len(batch)} complaints.\n"]
    for t in batch:
        attrs = f'id="{t.trace_id}"'
        if prompt_version in ("route-v2", "route-v3"):
            attrs += f' company="{company_of(t)}"'
        parts.append(f'<complaint {attrs}>\n{truncate(t.input)}\n</complaint>\n')
    return "\n".join(parts)


def run(eval_dir: str | Path, run_dir: str | Path, *, model: str, split: str = "dev", version: str = "v1",
        start: int = 0, limit: int | None = None, batch_size: int = 10, seed: int = 0,
        prompt_version: str = "route-v1", workers: int = 4, effort: str | None = None) -> dict:
    assert prompt_version in PROMPT_VERSIONS
    eval_dir, run_dir = Path(eval_dir), Path(run_dir)
    test_path = verify_frozen(eval_dir, version, name=split)
    manifest = json.loads((eval_dir / f"{split}_{version}.manifest.json").read_text())
    labels = json.loads((eval_dir / f"labels_{version}.json").read_text())
    traces = list(read_traces(test_path))
    traces = traces[start : (start + limit) if limit else None]
    order = list(range(len(traces)))
    random.Random(seed).shuffle(order)
    batches = [[traces[i] for i in order[k : k + batch_size]] for k in range(0, len(order), batch_size)]

    system = system_prompt(labels, prompt_version)
    schema = answer_schema(labels)
    run_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "kind": "claude_baseline",
        "model": model,
        "prompt_version": prompt_version,
        "split": split,
        "slice": [start, start + len(traces)],
        "system_prompt_sha256": hashlib.sha256(system.encode()).hexdigest(),
        "test_sha256": manifest["test_sha256"],
        "n_items": len(traces),
        "batch_size": batch_size,
        "seed": seed,
        "max_words": MAX_WORDS,
        "effort": effort or "CLI default",
        "backend": f"claude CLI headless, runner v{claude_cli.RUNNER_VERSION}",
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2))
    (run_dir / "system_prompt.txt").write_text(system)

    def one(bi_batch):
        bi, batch = bi_batch
        t0 = time.time()
        r = claude_cli.call(user_prompt(batch, prompt_version), system=system, model=model, schema=schema,
                             effort=effort)
        return bi, batch, r, time.time() - t0

    preds, calls = {}, []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for bi, batch, r, dt in pool.map(one, enumerate(batches)):
            answers = r.data.get("answers", []) if isinstance(r.data, dict) else []
            ids = {t.trace_id for t in batch}
            for a in answers:
                if a.get("id") in ids:
                    preds[a["id"]] = {"product": a.get("product"), "issue": a.get("issue")}
            calls.append({"batch": bi, "n": len(batch), "n_answered": sum(1 for t in batch if t.trace_id in preds),
                          "usage": r.usage, "cost_usd_equiv": r.cost_usd_equiv, "models_used": r.models_used,
                          "cached": r.cached, "seconds": round(dt, 2)})
            print(f"batch {bi + 1}/{len(batches)}: {calls[-1]['n_answered']}/{len(batch)} answered"
                  f"{' (cached)' if r.cached else f' in {dt:.0f}s'}", flush=True)

    with open(run_dir / "predictions.jsonl", "w") as f:
        for t in traces:
            f.write(json.dumps({"trace_id": t.trace_id, "pred": preds.get(t.trace_id), "gold": {
                "product": t.output["product"], "issue": t.output["issue"]}}) + "\n")
    with open(run_dir / "calls.jsonl", "w") as f:
        for c in calls:
            f.write(json.dumps(c) + "\n")
    return config
