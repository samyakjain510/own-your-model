# Own Your Model: serving-throughput benchmark on a Kaggle T4.
#
# Question for the cost model: how many complaints per second can ONE cheap GPU
# answer with the fine-tuned model?
#
# Two engines, run as SEPARATE Kaggle jobs (CONFIG["engine"]), because installing
# vLLM changed shared packages and broke the plain Hugging Face test the first time:
#   "hf":   Hugging Face generate, fp16, adapter merged in, complaints sorted by length
#           so each batch has little padding (fine for offline batch work).
#   "vllm": vLLM with the LoRA adapter. The T4 is an older GPU, so we try a few
#           setups in turn, each in its own process, and keep the first that works.
# Every result file says which engine and setup produced it.
#
# CONFIG is filled in by scripts/kaggle_push_bench.py.

CONFIG = {}  # injected

import glob
import json
import os
import subprocess
import sys
import time
import traceback

OUT = "/kaggle/working/bench"
os.makedirs(OUT, exist_ok=True)
dev_path = glob.glob("/kaggle/input/**/dev_prompts.jsonl", recursive=True)[0]
adapter = sorted(glob.glob(f"/kaggle/input/**/results/{CONFIG['adapter_run']}/adapter", recursive=True))[0]
print("dev:", dev_path, "| adapter:", adapter, flush=True)


def record(name, payload):
    with open(os.path.join(OUT, f"{name}.json"), "w") as f:
        json.dump({**payload, "config": CONFIG}, f, indent=2)
    print(name, json.dumps(payload)[:800], flush=True)


def versions(*pkgs):
    import importlib.metadata as md
    out = {}
    for p in pkgs:
        try:
            out[p] = md.version(p)
        except Exception:
            out[p] = None
    return out


if CONFIG["engine"] == "hf":
    try:
        # peft refuses to load if an old torchao is present; it doesn't need torchao at all.
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"])
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        rows = [json.loads(line) for line in open(dev_path)][: CONFIG["n_items"]]
        tok = AutoTokenizer.from_pretrained(CONFIG["base_model"])
        tok.padding_side = "left"
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        model = AutoModelForCausalLM.from_pretrained(CONFIG["base_model"], torch_dtype=torch.float16, device_map="cuda:0")
        model = PeftModel.from_pretrained(model, adapter).merge_and_unload().eval()
        prompts = [tok.apply_chat_template(r["ft_messages"], tokenize=False, add_generation_prompt=True) for r in rows]
        prompts.sort(key=lambda p: len(tok(p).input_ids))
        results = {}
        for bs in CONFIG["hf_batch_sizes"]:
            try:
                torch.cuda.synchronize()
                t0 = time.time()
                n_out = 0
                for i in range(0, len(prompts), bs):
                    enc = tok(prompts[i : i + bs], return_tensors="pt", padding=True).to("cuda")
                    with torch.no_grad():
                        out = model.generate(**enc, max_new_tokens=64, do_sample=False, pad_token_id=tok.pad_token_id)
                    n_out += int((out[:, enc["input_ids"].shape[1]:] != tok.pad_token_id).sum())
                torch.cuda.synchronize()
                secs = time.time() - t0
                results[str(bs)] = {"seconds": round(secs, 2), "items_per_second": round(len(prompts) / secs, 3),
                                    "output_tokens": n_out,
                                    "peak_gpu_memory_gb": round(torch.cuda.max_memory_reserved() / 1e9, 2)}
            except torch.cuda.OutOfMemoryError:
                results[str(bs)] = {"error": "out of GPU memory"}
                torch.cuda.empty_cache()
            print("hf batch", bs, results[str(bs)], flush=True)
        record("hf_generate", {"engine": "transformers generate, fp16, merged adapter, length-sorted batches",
                               "items": len(prompts), "by_batch_size": results, "gpu": torch.cuda.get_device_name(0),
                               "versions": versions("torch", "transformers", "peft")})
    except Exception:
        record("hf_failed", {"engine": "hf", "error": traceback.format_exc()[-3000:]})

else:
    INNER = r'''
import json, sys, time, importlib.metadata as md
cfg, dev_path, adapter, out_path = json.loads(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest
rows = [json.loads(line) for line in open(dev_path)][: cfg["n_items"]]
llm = LLM(model=cfg["base_model"], dtype="half", enable_lora=True, max_lora_rank=16, max_model_len=1536,
          gpu_memory_utilization=0.90, enforce_eager=True, seed=0)
tok = llm.get_tokenizer()
prompts = [tok.apply_chat_template(r["ft_messages"], tokenize=False, add_generation_prompt=True) for r in rows]
sp = SamplingParams(temperature=0.0, max_tokens=64)
lora = LoRARequest("ft", 1, adapter)
llm.generate(prompts[:8], sp, lora_request=lora)
t0 = time.time()
outs = llm.generate(prompts, sp, lora_request=lora)
secs = time.time() - t0
n_out = sum(len(o.outputs[0].token_ids) for o in outs)
with open(out_path, "w") as f:
    json.dump({"items": len(rows), "seconds": round(secs, 2), "items_per_second": round(len(rows) / secs, 3),
               "prompt_tokens": sum(len(o.prompt_token_ids) for o in outs), "output_tokens": n_out,
               "output_tokens_per_second": round(n_out / secs, 1), "vllm_version": md.version("vllm"),
               "sample_outputs": [o.outputs[0].text[:200] for o in outs[:5]]}, f)
'''
    inner_path = "/kaggle/working/vllm_inner.py"
    open(inner_path, "w").write(INNER)
    attempts = CONFIG["vllm_attempts"]
    tried = []
    for a in attempts:
        print("=== vLLM attempt:", a, flush=True)
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + a["pip"], capture_output=True, text=True)
        if r.returncode != 0:
            tried.append({**a, "result": "pip install failed", "stderr": r.stderr[-1500:]})
            continue
        env = {**os.environ, **a.get("env", {})}
        out_path = os.path.join(OUT, "vllm_raw.json")
        r = subprocess.run([sys.executable, inner_path, json.dumps(CONFIG), dev_path, adapter, out_path],
                           capture_output=True, text=True, env=env, timeout=3600)
        if r.returncode == 0 and os.path.exists(out_path):
            res = json.load(open(out_path))
            record("vllm", {"engine": "vllm", "setup": a, "gpu": "Tesla T4", "dtype": "float16",
                            "adapter": CONFIG["adapter_run"], **res, "earlier_attempts": tried})
            break
        tried.append({**a, "result": f"exit {r.returncode}", "stderr": r.stderr[-2500:]})
    else:
        record("vllm_failed", {"engine": "vllm", "attempts": tried})

print("ALL DONE", flush=True)
