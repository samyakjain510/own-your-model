"""Own-vs-rent cost model.

Everything is per 1,000 tasks (here, 1,000 complaints routed), built from:
- token counts and throughput MEASURED in our runs (runs/*), and
- published prices (configs/cost_inputs.json, each with a source link).

Options:
  (a) rent Claude: measured tokens x list price, with the Batch API discount;
      prompt caching is already reflected in the measured cache-read tokens.
  (b) rent an open model per token: the base small model with Claude's long
      label-list prompt (it isn't fine-tuned), at a hosted per-token price.
  (c) self-host a GPU: the GPU is paid for every hour of the month whether busy
      or idle. Cost per task depends on volume.
  (d) the fine-tuned small model on the cheaper of per-token hosting or (c).
      Its prompt is short (no label list), so it needs fewer tokens per task.

Engineering time (an assumption) is added to the own options as a monthly cost.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ClaudeProfile:
    """Average tokens per task, split the way Claude bills them."""
    input: float
    cache_write: float
    cache_read: float
    output: float
    n_tasks: int
    source_run: str


def claude_profile_from_run(run_dir: str | Path) -> ClaudeProfile:
    run_dir = Path(run_dir)
    calls = [json.loads(line) for line in open(run_dir / "calls.jsonl")]
    n = sum(c["n"] for c in calls)
    tot = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    for c in calls:
        u = c["usage"]
        tot["input"] += u.get("input_tokens", 0)
        tot["cache_write"] += u.get("cache_creation_input_tokens", 0)
        tot["cache_read"] += u.get("cache_read_input_tokens", 0)
        tot["output"] += u.get("output_tokens", 0)
    return ClaudeProfile(**{k: v / n for k, v in tot.items()}, n_tasks=n, source_run=str(run_dir.relative_to(ROOT)))


def claude_cost_per_1k(p: ClaudeProfile, price: dict, batch_discount: float = 0.0) -> float:
    per_task = (p.input * price["input"] + p.cache_write * price["cache_write_5m"]
                + p.cache_read * price["cache_read"] + p.output * price["output"]) / 1e6
    return per_task * 1000 * (1 - batch_discount)


def per_token_cost_per_1k(prompt_tokens: float, output_tokens: float, price: dict) -> float:
    return (prompt_tokens * price["input"] + output_tokens * price["output"]) / 1e6 * 1000


def self_host_monthly(volume: float, items_per_second: float, gpu_hourly: float, hours: float = 730,
                      max_util: float = 0.6) -> tuple[float, int]:
    """Monthly GPU bill and GPU count to serve `volume` tasks/month. Always at least one GPU, always on."""
    capacity = items_per_second * 3600 * hours * max_util
    gpus = max(1, math.ceil(volume / capacity))
    return gpus * gpu_hourly * hours, gpus


def engineering_monthly(e: dict) -> float:
    return e["loaded_cost_per_day_usd"] * (e["build_days"] / e["amortize_build_over_months"] + e["maintain_days_per_month"])


def break_even(rent_per_1k: float, own_monthly_fn, lo: float = 1e3, hi: float = 1e9) -> float | None:
    """Smallest monthly volume where owning costs no more than renting (search on a log grid)."""
    v = lo
    while v <= hi:
        if own_monthly_fn(v) <= rent_per_1k * v / 1000:
            return v
        v *= 1.05
    return None


def report(claude_runs: dict[str, str], small_ft_result: str, small_zs_result: str | None,
           inputs_path: str | Path = ROOT / "configs" / "cost_inputs.json",
           volumes=(10_000, 100_000, 1_000_000, 10_000_000)) -> dict:
    inp = json.loads(Path(inputs_path).read_text())
    disc = inp["batch_discount"]["value"]
    eng = engineering_monthly(inp["engineering"])
    gpu_name, gpu = min(inp["gpu_hourly"].items(), key=lambda kv: kv[1]["usd_per_hour"])
    util = inp["self_host"]["max_utilization"]["value"]

    out = {"inputs": {"gpu": gpu_name, "gpu_usd_per_hour": gpu["usd_per_hour"], "max_utilization": util,
                      "engineering_usd_per_month (assumption)": round(eng), "batch_discount": disc},
           "per_1k": {}, "monthly_at_volume": {}, "break_even_monthly_volume": {}}

    rent = {}
    for model, run in claude_runs.items():
        prof = claude_profile_from_run(ROOT / run)
        price = inp["claude_prices_per_mtok"][model]
        rent[f"(a) {model}, batch"] = claude_cost_per_1k(prof, price, disc)
        out["per_1k"][f"(a) {model}, standard"] = round(claude_cost_per_1k(prof, price, 0.0), 4)
        out.setdefault("claude_tokens_per_task", {})[model] = {k: round(getattr(prof, k), 1) for k in
                                                                ("input", "cache_write", "cache_read", "output")}

    ft = json.loads(Path(ROOT / small_ft_result).read_text())["timing"]
    ft_in, ft_out = ft["prompt_tokens"] / ft["items"], ft["output_tokens"] / ft["items"]
    hosted = inp["hosted_open_model_per_mtok"]
    if small_zs_result:
        zs = json.loads(Path(ROOT / small_zs_result).read_text())["timing"]
        rent["(b) open model per token, label-list prompt"] = per_token_cost_per_1k(
            zs["prompt_tokens"] / zs["items"], zs["output_tokens"] / zs["items"], hosted)
    ft_hosted = per_token_cost_per_1k(ft_in, ft_out, hosted)
    out["small_model_tokens_per_task"] = {"fine_tuned": {"prompt": round(ft_in, 1), "output": round(ft_out, 1)}}
    out["measured_items_per_second_T4"] = ft["items_per_second"]
    for k, v in rent.items():
        out["per_1k"][k] = round(v, 4)
    out["per_1k"]["(d) fine-tuned, hosted per token (unverified that a host serves this adapter)"] = round(ft_hosted, 4)

    def own_gpu(v):
        return self_host_monthly(v, ft["items_per_second"], gpu["usd_per_hour"], inp["self_host"]["hours_per_month"], util)[0] + eng

    def own_hosted(v):
        return ft_hosted * v / 1000 + eng

    for v in volumes:
        row = {k: round(c * v / 1000, 2) for k, c in rent.items()}
        gpu_bill, n_gpus = self_host_monthly(v, ft["items_per_second"], gpu["usd_per_hour"],
                                             inp["self_host"]["hours_per_month"], util)
        row[f"(c/d) fine-tuned on own {gpu_name} x{n_gpus} + engineering"] = round(gpu_bill + eng, 2)
        row["(d) fine-tuned hosted per token + engineering"] = round(own_hosted(v), 2)
        out["monthly_at_volume"][f"{v:,}/month"] = row

    for k, r in rent.items():
        be_gpu = break_even(r, own_gpu)
        be_host = break_even(r, own_hosted)
        out["break_even_monthly_volume"][k] = {
            "vs own GPU": f"{be_gpu:,.0f}/month" if be_gpu else "never below 1B/month",
            "vs hosted fine-tuned": f"{be_host:,.0f}/month" if be_host else "never below 1B/month"}
    return out
