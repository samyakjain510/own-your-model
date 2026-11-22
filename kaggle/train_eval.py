# Own Your Model: LoRA fine-tune + dev evaluation on a Kaggle T4 GPU.
#
# Runs in the cloud, never on the laptop. For each training-set size:
#   1. load the base model in 4-bit, attach a LoRA adapter (Unsloth),
#   2. train up to 2 passes over the data, checking validation loss as it goes,
#      and keep the checkpoint with the lowest validation loss,
#   3. answer every dev complaint with greedy decoding and save predictions,
#      prompt/answer token counts and wall-clock timings.
# Optionally also tests the base model before any training ("zero-shot"),
# using the same label-list prompt Claude gets.
#
# CONFIG is filled in by scripts/kaggle_push.py.

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
from unsloth.chat_templates import train_on_responses_only  # noqa: E402
import torch  # noqa: E402
from datasets import Dataset  # noqa: E402
from trl import SFTConfig, SFTTrainer  # noqa: E402

OUT = "/kaggle/working/results"
os.makedirs(OUT, exist_ok=True)
data_dir = os.path.dirname(glob.glob("/kaggle/input/**/train_500.jsonl", recursive=True)[0])
print("data dir:", data_dir, "| config:", CONFIG, flush=True)


def read_jsonl(name):
    with open(os.path.join(data_dir, name)) as f:
        return [json.loads(line) for line in f if line.strip()]


def env_info():
    import importlib.metadata as md
    info = {"gpu": torch.cuda.get_device_name(0), "torch": torch.__version__}
    for pkg in ("unsloth", "transformers", "trl", "peft", "bitsandbytes"):
        try:
            info[pkg] = md.version(pkg)
        except Exception:
            info[pkg] = None
    return info


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
    timing = {"items": len(rows), "seconds": round(secs, 1), "items_per_second": round(len(rows) / secs, 3),
              "prompt_tokens": n_in, "output_tokens": n_out, "output_tokens_per_second": round(n_out / secs, 1),
              "batch_size": batch_size}
    return preds, timing


def save(run, preds, timing, extra):
    d = os.path.join(OUT, run)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "predictions.jsonl"), "w") as f:
        for p in preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(os.path.join(d, "result.json"), "w") as f:
        json.dump({"timing": timing, **extra, "env": env_info(), "config": CONFIG}, f, indent=2)
    print(run, "saved:", timing, flush=True)


dev = read_jsonl("dev_prompts.jsonl")[: CONFIG["dev_limit"]]

if CONFIG.get("zero_shot_limit"):
    model, tok = FastLanguageModel.from_pretrained(CONFIG["model"], max_seq_length=4096, load_in_4bit=True)
    preds, timing = predict(model, tok, dev[: CONFIG["zero_shot_limit"]], "zs_messages", 4096, 4)
    save(f"{CONFIG['tag']}-zeroshot", preds, timing, {"kind": "zero_shot"})
    del model
    torch.cuda.empty_cache()

for n in CONFIG["sizes"]:
    run = f"{CONFIG['tag']}-n{n}"
    model, tok = FastLanguageModel.from_pretrained(CONFIG["model"], max_seq_length=1024, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(
        model, r=16, lora_alpha=16, lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth", random_state=CONFIG["seed"])

    def fmt(ex):
        # Qwen3's chat template puts an empty "<think>\n\n</think>\n\n" before the final answer.
        # Strip it so the model learns to output only the JSON, matching the inference prompt.
        text = tok.apply_chat_template(ex["messages"], tokenize=False)
        return {"text": text.replace("<think>\n\n</think>\n\n", "")}

    train_ds = Dataset.from_list([{"messages": r["messages"]} for r in read_jsonl(f"train_{n}.jsonl")]).map(fmt)
    val_ds = Dataset.from_list([{"messages": r["messages"]} for r in read_jsonl("val.jsonl")][: CONFIG["val_limit"]]).map(fmt)
    eff_batch = 8
    steps = min(CONFIG["epochs"] * n // eff_batch, CONFIG["max_steps"])
    eval_every = max(10, steps // 8)
    common = dict(
        per_device_train_batch_size=4, gradient_accumulation_steps=2, per_device_eval_batch_size=8,
        max_steps=steps, learning_rate=2e-4, lr_scheduler_type="linear", warmup_steps=max(1, steps // 20),
        logging_steps=max(1, eval_every // 2), eval_strategy="steps", eval_steps=eval_every,
        save_strategy="steps", save_steps=eval_every, save_total_limit=2, load_best_model_at_end=True,
        metric_for_best_model="eval_loss", greater_is_better=False,
        fp16=not torch.cuda.is_bf16_supported(), bf16=torch.cuda.is_bf16_supported(),
        seed=CONFIG["seed"], output_dir=f"/kaggle/tmp/{run}", report_to="none", dataset_text_field="text")
    try:
        args = SFTConfig(max_length=1024, **common)
    except TypeError:
        args = SFTConfig(max_seq_length=1024, **common)
    try:
        trainer = SFTTrainer(model=model, processing_class=tok, train_dataset=train_ds, eval_dataset=val_ds, args=args)
    except TypeError:
        trainer = SFTTrainer(model=model, tokenizer=tok, train_dataset=train_ds, eval_dataset=val_ds, args=args)
    trainer = train_on_responses_only(trainer, instruction_part="<|im_start|>user\n",
                                      response_part="<|im_start|>assistant\n")
    torch.cuda.synchronize()
    t0 = time.time()
    trainer.train()
    torch.cuda.synchronize()
    train_secs = time.time() - t0
    log = trainer.state.log_history
    evals = [(e["step"], e["eval_loss"]) for e in log if "eval_loss" in e]
    model.save_pretrained(os.path.join(OUT, run, "adapter"))
    tok.save_pretrained(os.path.join(OUT, run, "adapter"))
    preds, timing = predict(model, tok, dev, "ft_messages", 1024, 16)
    save(run, preds, timing, {
        "kind": "lora", "n_train": n, "steps": steps, "effective_batch": eff_batch, "train_seconds": round(train_secs, 1),
        "best_checkpoint": trainer.state.best_model_checkpoint, "best_eval_loss": trainer.state.best_metric,
        "eval_loss_by_step": evals, "peak_gpu_memory_gb": round(torch.cuda.max_memory_reserved() / 1e9, 2),
        "lora": {"r": 16, "alpha": 16, "targets": "all linear"}, "learning_rate": 2e-4})
    del model, trainer
    torch.cuda.empty_cache()

print("ALL DONE", flush=True)
