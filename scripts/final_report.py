#!/usr/bin/env python3
"""Score every test run the way docs/phase4/locked-choices.md says, and save one summary.

  PYTHONPATH=src python3 scripts/final_report.py

Writes runs/final/summary.json. Every number in the write-up comes from that file.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oym.audit import audited_scores, paired_audited  # noqa: E402
from oym.compare import paired  # noqa: E402
from oym.cost import report  # noqa: E402
from oym.score import score  # noqa: E402

LABELS = ROOT / "data" / "eval" / "labels_v2.json"
K = ROOT / "runs" / "kaggle" / "oym-test-v2" / "test_results"
RUNS = {
    "Qwen3-4B trained on 8,000": K / "test-qwen3-4b-n8000",
    "Qwen3-4B trained on 2,000": K / "test-qwen3-4b-n2000",
    "Qwen3-4B trained on 500": K / "test-qwen3-4b-n500",
    "Qwen3-4B, no training": K / "test-qwen3-4b-zeroshot",
    "Claude Haiku 5.5": ROOT / "runs" / "test-haiku55-route-v2-n800",
    "Claude Sonnet 5.5": ROOT / "runs" / "test-sonnet55-route-v2-n800",
}
MAIN, RENT = "Qwen3-4B trained on 8,000", "Claude Haiku 5.5"
AUDIT = ROOT / "runs" / "audit-test-opus55"


def rel(p):
    return str(Path(p).relative_to(ROOT))


def main():
    have = {k: v for k, v in RUNS.items() if (v / "predictions.jsonl").exists()}
    missing = sorted(set(RUNS) - set(have))
    out = {"split": "test_v2 (800 complaints, Apr 1 - Aug 14 2026)", "locked_choices": "docs/phase4/locked-choices.md",
           "missing_runs": missing, "scores": {}, "head_to_head_vs_haiku": {}, "audited": {}}
    for name, d in have.items():
        s = score(d, LABELS)
        out["scores"][name] = {"run": rel(d), "product": s["product_accuracy"],
                               "product_and_issue": s["product_and_issue_accuracy"],
                               "missing": s["missing_answers"], "invalid_pairs": s["invalid_issue_for_product"]}
    if RENT in have:
        for name, d in have.items():
            if name != RENT:
                out["head_to_head_vs_haiku"][name] = paired(d, have[RENT])
    if (AUDIT / "verdicts.jsonl").exists():
        out["audited"]["checker_verdicts"] = json.loads((AUDIT / "config.json").read_text())["verdict_counts"]
        for name, d in have.items():
            out["audited"][name] = audited_scores(d, AUDIT)
        if MAIN in have and RENT in have:
            out["audited"]["main_vs_haiku_paired"] = paired_audited(have[MAIN], have[RENT], AUDIT)
    if MAIN in have and RENT in have:
        out["cost"] = report(
            {"Claude Haiku 5.5 (test run)": ("claude-haiku-5-5", rel(have[RENT]))},
            rel(have[MAIN] / "result.json"),
            rel(have["Qwen3-4B, no training"] / "result.json") if "Qwen3-4B, no training" in have else None,
            throughput=(2.395, "runs/kaggle/oym-bench-hf-qwen3-4b-n8000/bench/hf_generate.json "
                               "(HF generate fp16, merged adapter, length-sorted, batch 16, Tesla T4)"),
            gpu_name="T4 (AWS g4dn.xlarge)", volumes=(100_000, 1_000_000, 10_000_000, 100_000_000))
        if "Claude Sonnet 5.5" in have:
            out["cost_sonnet_reference"] = report(
                {"Claude Sonnet 5.5 (test run)": ("claude-sonnet-5-5", rel(have["Claude Sonnet 5.5"]))},
                rel(have[MAIN] / "result.json"), None, throughput=(2.395, "same as above"),
                gpu_name="T4 (AWS g4dn.xlarge)")["per_1k"]
    dest = ROOT / "runs" / "final"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "summary.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"missing_runs": missing, "scores": out["scores"]}, indent=1))


if __name__ == "__main__":
    main()
