#!/usr/bin/env python3
"""Push kaggle/serve_bench.py as a PRIVATE Kaggle script (T4), reading the adapter from a finished training job.

  python scripts/kaggle_push_bench.py qwen3-4b-n8000 oym-qwen3-4b-b hf
  python scripts/kaggle_push_bench.py qwen3-4b-n8000 oym-qwen3-4b-b vllm

The two engines run as separate jobs: installing vLLM changed shared packages and
broke the Hugging Face test when both ran in one job.
"""

# vLLM setups to try in order on the T4 (an older GPU that the newest vLLM's fast paths skip).
VLLM_ATTEMPTS = [
    {"pip": ["vllm", "nvidia-cutlass-dsl"], "env": {"VLLM_ATTENTION_BACKEND": "TRITON_ATTN"}},
    {"pip": ["vllm", "nvidia-cutlass-dsl"], "env": {"VLLM_ATTENTION_BACKEND": "FLEX_ATTENTION"}},
    {"pip": ["vllm==0.10.2"], "env": {"VLLM_ATTENTION_BACKEND": "XFORMERS"}},
]

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "samyakjain510"


def main():
    adapter_run, source_kernel, engine = sys.argv[1], sys.argv[2], sys.argv[3]
    assert engine in ("hf", "vllm")
    cfg = {"engine": engine, "adapter_run": adapter_run, "base_model": "Qwen/Qwen3-4B-Instruct-2507", "n_items": 800,
           "hf_batch_sizes": [16, 32, 64, 128], "vllm_attempts": VLLM_ATTEMPTS}
    slug = f"oym-bench-{engine}-{adapter_run}"
    folder = ROOT / "data" / "kaggle" / "kernels" / slug
    folder.mkdir(parents=True, exist_ok=True)
    code = (ROOT / "kaggle" / "serve_bench.py").read_text().replace("CONFIG = {}  # injected", f"CONFIG = {cfg!r}")
    (folder / "serve_bench.py").write_text(code)
    (folder / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{OWNER}/{slug}", "title": slug, "code_file": "serve_bench.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_tpu": False, "enable_internet": True,
        "dataset_sources": [f"{OWNER}/oym-cfpb-routing-v1"], "competition_sources": [],
        "kernel_sources": [f"{OWNER}/{source_kernel}"], "model_sources": [],
    }, indent=2))
    r = subprocess.run([str(ROOT / ".venv" / "bin" / "kaggle"), "kernels", "push", "-p", str(folder),
                        "--accelerator", "NvidiaTeslaT4"], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())


if __name__ == "__main__":
    main()
