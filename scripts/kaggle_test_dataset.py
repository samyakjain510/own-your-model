#!/usr/bin/env python3
"""Pack the sealed test set's prompts for a SEPARATE private Kaggle dataset, for the final run only.

Same prompt formats as the dev prompts (scripts/kaggle_dataset.py). Before packing,
it re-runs the leakage guard: no test complaint may match a training complaint
exactly or nearly. It refuses to pack if one does.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oym.baseline import system_prompt  # noqa: E402
from oym.leakage import assert_no_leakage  # noqa: E402
from oym.schema import read_traces  # noqa: E402
from oym.split import verify_frozen  # noqa: E402
from oym.trainset import SYSTEM, user_text  # noqa: E402

OWNER = "samyakjain510"
SLUG = "oym-cfpb-routing-test-v2"


def main():
    test_path = verify_frozen(ROOT / "data" / "eval", "v2", name="test")
    tests = list(read_traces(test_path))
    train = {}
    for line in open(ROOT / "data" / "train" / "train_8000.jsonl"):
        r = json.loads(line)
        train[r["trace_id"]] = r["messages"][1]["content"].partition("\n\nComplaint:\n")[2]
    assert_no_leakage(train, {t.trace_id: t.input for t in tests})
    print(f"leakage check passed: {len(tests)} test vs {len(train)} training complaints")

    out = ROOT / "data" / "kaggle" / "test_dataset"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    labels = json.loads((ROOT / "data" / "eval" / "labels_v2.json").read_text())
    zs_system = system_prompt(labels, "route-v2").rsplit("\n", 1)[0] + (
        '\nReply with JSON only: {"product": "...", "issue": "..."}')
    with open(out / "test_prompts.jsonl", "w", encoding="utf-8") as f:
        for t in tests:
            company = t.context.get("company") or t.metadata.get("company")
            u = user_text(company, t.input)
            f.write(json.dumps({
                "trace_id": t.trace_id,
                "gold": {"product": t.output["product"], "issue": t.output["issue"]},
                "ft_messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": u}],
                "zs_messages": [{"role": "system", "content": zs_system}, {"role": "user", "content": u}],
            }, ensure_ascii=False) + "\n")
    (out / "dataset-metadata.json").write_text(json.dumps(
        {"title": SLUG, "id": f"{OWNER}/{SLUG}", "licenses": [{"name": "CC0-1.0"}]}, indent=2))
    if "--upload" in sys.argv:
        r = subprocess.run([str(ROOT / ".venv" / "bin" / "kaggle"), "datasets", "create", "-p", str(out)],
                           capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())


if __name__ == "__main__":
    main()
