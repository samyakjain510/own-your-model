#!/usr/bin/env python3
"""Push kaggle/test_eval.py as a PRIVATE Kaggle script (T4): the small models on the sealed test set.

  python scripts/kaggle_push_test.py
"""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "samyakjain510"
SLUG = "oym-test-v2"
CFG = {"adapters": ["qwen3-4b-n8000", "qwen3-4b-n2000", "qwen3-4b-n500"], "zero_shot": True,
       "base_model": "unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit"}


def main():
    folder = ROOT / "data" / "kaggle" / "kernels" / SLUG
    folder.mkdir(parents=True, exist_ok=True)
    code = (ROOT / "kaggle" / "test_eval.py").read_text().replace("CONFIG = {}  # injected", f"CONFIG = {CFG!r}")
    (folder / "test_eval.py").write_text(code)
    (folder / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{OWNER}/{SLUG}", "title": SLUG, "code_file": "test_eval.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": True,
        "dataset_sources": [f"{OWNER}/oym-cfpb-routing-test-v2"], "competition_sources": [],
        "kernel_sources": [f"{OWNER}/oym-qwen3-4b-a", f"{OWNER}/oym-qwen3-4b-b"], "model_sources": [],
    }, indent=2))
    r = subprocess.run([str(ROOT / ".venv" / "bin" / "kaggle"), "kernels", "push", "-p", str(folder),
                        "--accelerator", "NvidiaTeslaT4"], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())


if __name__ == "__main__":
    main()
