# Own Your Model: FINAL run of the small models on the sealed test set (Kaggle T4).
#
# Loads the trained adapters from the earlier training jobs (no retraining), answers
# every test complaint with greedy decoding, and saves predictions and timings.
# The base model with no training uses the label-list prompt. Same code path as the
# dev evaluation in kaggle/train_eval.py.
#
# CONFIG is filled in by scripts/kaggle_push_test.py.

CONFIG = {}  # injected

import glob
import json
import os
import re
import subprocess
import sys
import time

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "unsloth"], check=True)

from unsloth import FastLanguageModel  # noqa: E402
import torch  # noqa: E402

OUT = "/kaggle/working/test_results"
os.makedirs(OUT, exist_ok=True)
test = [json.loads(l) for l in open(glob.glob("/kaggle/input/**/test_prompts.jsonl", recursive=True)[0])]
print("test items:", len(test), flush=True)
JSON_RE = re.compile(r"\{.*?\}", re.S)


def parse(text):
    m = JSON_RE.search(text)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return {"product": d.get("product"), "issue": d.get("issue")}
    except Exception:
        return None


def predict(model, tok, rows, key, max_len, batch_size):
    FastLanguageModel.for_inference(model)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    preds, n_in, n_out = [], 0, 0
    torch.cuda.synchronize()
    t0 = time.time()
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        prompts = [tok.apply_chat_template(r[key], tokenize=False, add_generation_prompt=True) for r in batch]
        enc = tok(prompts, return_tensors="pt", padding=True, truncation=True, max_length=max_len).to("cuda")
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=64, do_sample=False, pad_token_id=tok.pad_token_id)
        new = out[:, enc["input_ids"].shape[1]:]
        n_in += int(enc["attention_mask"].sum())
        for r, ids in zip(batch, new):
            text = tok.decode(ids, skip_special_tokens=True)
            n_out += int((ids != tok.pad_token_id).sum())
            preds.append({"trace_id": r["trace_id"], "pred": parse(text), "raw": text[:300], "gold": r["gold"]})
    torch.cuda.synchronize()
    secs = time.time() - t0
    return preds, {"items": len(rows), "seconds": round(secs, 1), "items_per_second": round(len(rows) / secs, 3),
                   "prompt_tokens": n_in, "output_tokens": n_out, "batch_size": batch_size}


def save(run, preds, timing, extra):
    d = os.path.join(OUT, run)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "predictions.jsonl"), "w") as f:
        for p in preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(os.path.join(d, "result.json"), "w") as f:
        json.dump({"timing": timing, **extra, "split": "test_v2", "config": CONFIG}, f, indent=2)
    print(run, "saved:", timing, flush=True)


for run in CONFIG["adapters"]:
    path = sorted(glob.glob(f"/kaggle/input/**/results/{run}/adapter", recursive=True))[0]
    model, tok = FastLanguageModel.from_pretrained(path, max_seq_length=1024, load_in_4bit=True)
    preds, timing = predict(model, tok, test, "ft_messages", 1024, 16)
    save(f"test-{run}", preds, timing, {"kind": "lora", "adapter": run, "adapter_path": path})
    del model
    torch.cuda.empty_cache()

if CONFIG.get("zero_shot"):
    model, tok = FastLanguageModel.from_pretrained(CONFIG["base_model"], max_seq_length=4096, load_in_4bit=True)
    preds, timing = predict(model, tok, test, "zs_messages", 4096, 4)
    save("test-qwen3-4b-zeroshot", preds, timing, {"kind": "zero_shot"})

print("ALL DONE", flush=True)
