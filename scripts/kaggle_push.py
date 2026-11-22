#!/usr/bin/env python3
"""Push kaggle/train_eval.py as a PRIVATE Kaggle script on a T4 GPU, with a run config baked in.

  python scripts/kaggle_push.py smoke   # ~20-30 min check that everything runs
  python scripts/kaggle_push.py full    # zero-shot + learning curve 500 / 2,000 / 8,000

Nothing runs on this laptop: Kaggle runs it in the cloud. Fetch results with
  kaggle kernels output samyakjain510/<slug> -p runs/kaggle/<slug>
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "samyakjain510"
DATASET = f"{OWNER}/oym-cfpb-routing-v1"

PRESETS = {
    "smoke": {"tag": "qwen3-4b-smoke", "model": "unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit",
              "sizes": [500], "epochs": 2, "max_steps": 30, "dev_limit": 64, "val_limit": 64,
              "zero_shot_limit": 16, "seed": 0},
    "full": {"tag": "qwen3-4b", "model": "unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit",
             "sizes": [500, 2000, 8000], "epochs": 2, "max_steps": 2000, "dev_limit": 800, "val_limit": 300,
             "zero_shot_limit": 800, "seed": 0},
}


def main():
    preset = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    cfg = PRESETS[preset]
    slug = f"oym-{cfg['tag']}"
    folder = ROOT / "data" / "kaggle" / "kernels" / slug
    folder.mkdir(parents=True, exist_ok=True)
    code = (ROOT / "kaggle" / "train_eval.py").read_text().replace("CONFIG = {}  # injected", f"CONFIG = {json.dumps(cfg)}")
    (folder / "train_eval.py").write_text(code)
    (folder / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{OWNER}/{slug}", "title": slug, "code_file": "train_eval.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_tpu": False,
        "enable_internet": True, "dataset_sources": [DATASET], "competition_sources": [],
        "kernel_sources": [], "model_sources": [],
    }, indent=2))
    kaggle = ROOT / ".venv" / "bin" / "kaggle"
    r = subprocess.run([str(kaggle), "kernels", "push", "-p", str(folder), "--accelerator", "NvidiaTeslaT4"],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    (ROOT / "runs" / "kaggle").mkdir(parents=True, exist_ok=True)
    (ROOT / "runs" / "kaggle" / f"{slug}.pushed.json").write_text(json.dumps({"slug": slug, "config": cfg}, indent=2))


if __name__ == "__main__":
    main()
