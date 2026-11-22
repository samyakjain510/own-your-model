# Own Your Model: serving-throughput benchmark on a Kaggle T4.
#
# Question for the cost model: how many complaints per second can ONE cheap GPU
# answer with the fine-tuned model, using a real serving engine?
# Plan A: vLLM (fp16 base model + our LoRA adapter). Plan B, if vLLM can't run on
# a T4: plain Hugging Face generate at larger batch sizes. The result file says
# which engine produced each number.
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
adapters = sorted(glob.glob(f"/kaggle/input/**/results/{CONFIG['adapter_run']}/adapter", recursive=True))
print("dev:", dev_path, "| adapters:", adapters, flush=True)
adapter = adapters[0]
rows = [json.loads(line) for line in open(dev_path)][: CONFIG["n_items"]]


def record(name, payload):
    with open(os.path.join(OUT, f"{name}.json"), "w") as f:
        json.dump({**payload, "config": CONFIG}, f, indent=2)
    print(name, json.dumps(payload)[:600], flush=True)


# ---------- Plan A: vLLM ----------
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "vllm"], check=True)
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest
    import importlib.metadata as md

    llm = LLM(model=CONFIG["base_model"], dtype="half", enable_lora=True, max_lora_rank=16,
              max_model_len=1536, gpu_memory_utilization=0.90, enforce_eager=CONFIG.get("enforce_eager", True),
              seed=0)
    tok = llm.get_tokenizer()
    prompts = [tok.apply_chat_template(r["ft_messages"], tokenize=False, add_generation_prompt=True) for r in rows]
    sp = SamplingParams(temperature=0.0, max_tokens=64)
    lora = LoRARequest("ft", 1, adapter)
    llm.generate(prompts[:8], sp, lora_request=lora)  # warm-up
    t0 = time.time()
    outs = llm.generate(prompts, sp, lora_request=lora)
    secs = time.time() - t0
    n_in = sum(len(o.prompt_token_ids) for o in outs)
    n_out = sum(len(o.outputs[0].token_ids) for o in outs)
    preds = [{"trace_id": r["trace_id"], "raw": o.outputs[0].text[:200], "gold": r["gold"]} for r, o in zip(rows, outs)]
    with open(os.path.join(OUT, "vllm_predictions.jsonl"), "w") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")
    record("vllm", {"engine": "vllm", "vllm_version": md.version("vllm"), "items": len(rows), "seconds": round(secs, 2),
                    "items_per_second": round(len(rows) / secs, 2), "prompt_tokens": n_in, "output_tokens": n_out,
                    "output_tokens_per_second": round(n_out / secs, 1), "gpu": "Tesla T4", "dtype": "float16",
                    "adapter": CONFIG["adapter_run"]})
    del llm
except Exception:
    record("vllm_failed", {"engine": "vllm", "error": traceback.format_exc()[-3000:]})

# ---------- Plan B: Hugging Face generate, larger batches ----------
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    tok = AutoTokenizer.from_pretrained(CONFIG["base_model"])
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(CONFIG["base_model"], torch_dtype=torch.float16, device_map="cuda:0")
    model = PeftModel.from_pretrained(model, adapter).merge_and_unload().eval()
    prompts = [tok.apply_chat_template(r["ft_messages"], tokenize=False, add_generation_prompt=True) for r in rows]
    results = {}
    for bs in CONFIG["hf_batch_sizes"]:
        torch.cuda.synchronize()
        t0 = time.time()
        n_out = 0
        for i in range(0, len(prompts), bs):
            enc = tok(prompts[i : i + bs], return_tensors="pt", padding=True, truncation=True, max_length=1536).to("cuda")
            with torch.no_grad():
                out = model.generate(**enc, max_new_tokens=64, do_sample=False, pad_token_id=tok.pad_token_id)
            n_out += int((out[:, enc["input_ids"].shape[1]:] != tok.pad_token_id).sum())
        torch.cuda.synchronize()
        secs = time.time() - t0
        results[str(bs)] = {"seconds": round(secs, 2), "items_per_second": round(len(prompts) / secs, 2),
                            "output_tokens": n_out}
        print("hf batch", bs, results[str(bs)], flush=True)
    record("hf_generate", {"engine": "transformers generate, fp16, merged adapter", "items": len(prompts),
                           "by_batch_size": results, "gpu": "Tesla T4"})
except Exception:
    record("hf_failed", {"engine": "hf", "error": traceback.format_exc()[-3000:]})

print("ALL DONE", flush=True)
