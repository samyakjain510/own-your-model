"""Head-to-head comparison of runs on the SAME items (paired), plus a learning-curve table.

Paired means: for every complaint both models answered, we note who got it right,
then bootstrap the difference. That gives a tighter, fairer interval than comparing
two separate accuracy numbers.

  PYTHONPATH=src python -m oym.compare runs/dev-haiku55-route-v2-n300 runs/kaggle/.../qwen3-4b-n2000 ...
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .metrics import paired_diff_ci, wilson


def _load(run_dir: str | Path) -> dict[str, dict]:
    return {r["trace_id"]: r for r in (json.loads(line) for line in open(Path(run_dir) / "predictions.jsonl"))}


def _right(r: dict, level: str) -> bool:
    p, g = r.get("pred"), r["gold"]
    if not p:
        return False
    if level == "product":
        return p.get("product") == g["product"]
    return p.get("product") == g["product"] and p.get("issue") == g["issue"]


def paired(run_a: str | Path, run_b: str | Path) -> dict:
    a, b = _load(run_a), _load(run_b)
    ids = sorted(set(a) & set(b))
    out = {"a": str(run_a), "b": str(run_b), "n_shared": len(ids)}
    for level in ("product", "product_and_issue"):
        ca = [_right(a[i], level) for i in ids]
        cb = [_right(b[i], level) for i in ids]
        point, lo, hi = paired_diff_ci(ca, cb)
        out[level] = {"a": str(wilson(sum(ca), len(ids))), "b": str(wilson(sum(cb), len(ids))),
                      "a_minus_b": round(point, 3), "ci95": [round(lo, 3), round(hi, 3)],
                      "only_a_right": sum(x and not y for x, y in zip(ca, cb)),
                      "only_b_right": sum(y and not x for x, y in zip(ca, cb))}
    return out


if __name__ == "__main__":
    ref, *others = sys.argv[1:]
    print(json.dumps([paired(o, ref) for o in others], indent=2))
