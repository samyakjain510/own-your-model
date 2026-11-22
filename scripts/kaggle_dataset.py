#!/usr/bin/env python3
"""Pack training sets and dev prompts into a folder for a PRIVATE Kaggle dataset.

Dev prompts are built here, with the same code the rest of the kit uses, so the
cloud notebook never re-implements prompt formatting. Two prompt styles per dev
complaint:
- ft: the short prompt the fine-tuned model is trained on (company + complaint).
- zs: Claude's route-v2 system prompt with the full label list, for testing the
      small model before any training ("zero-shot").

The test set is not uploaded here. It goes up once, for the final run.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oym.baseline import system_prompt  # noqa: E402
from oym.schema import read_traces  # noqa: E402
from oym.split import verify_frozen  # noqa: E402
from oym.trainset import SYSTEM, user_text  # noqa: E402

OWNER = "samyakjain510"
SLUG = "oym-cfpb-routing-v1"


def main():
    out = ROOT / "data" / "kaggle" / "dataset"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in ("train_500", "train_2000", "train_8000", "val"):
        shutil.copy(ROOT / "data" / "train" / f"{name}.jsonl", out / f"{name}.jsonl")
    labels = json.loads((ROOT / "data" / "eval" / "labels_v1.json").read_text())
    shutil.copy(ROOT / "data" / "eval" / "labels_v1.json", out / "labels_v1.json")

    zs_system = system_prompt(labels, "route-v2").rsplit("\n", 1)[0] + (
        '\nReply with JSON only: {"product": "...", "issue": "..."}')
    dev_path = verify_frozen(ROOT / "data" / "eval", "v1", name="dev")
    with open(out / "dev_prompts.jsonl", "w", encoding="utf-8") as f:
        for t in read_traces(dev_path):
            company = t.context.get("company") or t.metadata.get("company")
            u = user_text(company, t.input)
            f.write(json.dumps({
                "trace_id": t.trace_id,
                "gold": {"product": t.output["product"], "issue": t.output["issue"]},
                "ft_messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": u}],
                "zs_messages": [{"role": "system", "content": zs_system}, {"role": "user", "content": u}],
            }, ensure_ascii=False) + "\n")

    (out / "dataset-metadata.json").write_text(json.dumps({
        "title": "oym-cfpb-routing-v1",
        "id": f"{OWNER}/{SLUG}",
        "licenses": [{"name": "CC0-1.0"}],
    }, indent=2))
    total = sum(p.stat().st_size for p in out.iterdir())
    print(f"packed {len(list(out.iterdir()))} files, {total / 1e6:.1f} MB -> {out}")


if __name__ == "__main__":
    main()
