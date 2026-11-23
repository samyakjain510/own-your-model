"""Call Claude through the Claude Code CLI in headless mode.

This project spends $0, so there is no API key. Instead we call `claude -p`,
which runs on the owner's Claude subscription. Each call:

- replaces Claude Code's default system prompt with ours (--system-prompt),
- turns off all tools (--tools ""), so it's a plain model call,
- asks for JSON that matches a schema (--json-schema),
- returns token usage, which the cost model multiplies by public API prices.

Every response is cached on disk by a hash of (model, system, prompt, schema),
so re-running an experiment never re-spends subscription usage.

Anyone with an API key can swap this module for the Anthropic SDK; the rest of
the kit only sees `call()`.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

RUNNER_VERSION = "2"  # bump when CLI flags change, so old cached answers are not reused
CACHE_DIR = Path(os.environ.get("OYM_CACHE", Path(__file__).resolve().parents[2] / "runs" / "_claude_cache"))


@dataclass
class ClaudeResult:
    data: object  # parsed JSON output
    model: str
    usage: dict
    cost_usd_equiv: float | None  # what this call would cost at API list price, as the CLI reports it
    cached: bool
    raw: dict
    models_used: list  # model IDs the CLI reports actually answering


def _key(model: str, system: str, prompt: str, schema: dict | None, effort: str | None = None) -> str:
    parts = [RUNNER_VERSION, model, system, prompt, schema] + ([f"effort={effort}"] if effort else [])
    blob = json.dumps(parts, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def call(prompt: str, *, system: str, model: str = "claude-haiku-5-5", schema: dict | None = None,
         timeout: int = 300, retries: int = 2, effort: str | None = None) -> ClaudeResult:
    """effort: the CLI's --effort level (low ... max). None keeps the CLI default.
    Lower effort means less thinking, so fewer output tokens."""
    key = _key(model, system, prompt, schema, effort)
    path = CACHE_DIR / key[:2] / f"{key}.json"
    if path.exists():
        raw = json.loads(path.read_text())
        return _parse(raw, model, cached=True)

    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("Claude Code CLI not found. Install it and log in, or use an API-key backend.")

    cmd = [exe, "-p", "--model", model, "--system-prompt", system, "--output-format", "json",
           "--tools", "", "--no-session-persistence",
           # Skip the user's MCP servers. Without this, every connected app's tool
           # definitions ride along: measured 281,839 prompt tokens per call vs 902 with it.
           "--strict-mcp-config"]
    if schema is not None:
        cmd += ["--json-schema", json.dumps(schema)]
    if effort:
        cmd += ["--effort", effort]

    # $0 rule: an API key in the environment would switch the CLI to paid API
    # billing, so strip it and use only the subscription login.
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    # Run from an empty folder so no CLAUDE.md, memory or project settings get
    # loaded into the prompt and inflate token counts.
    workdir = CACHE_DIR.parent / "_claude_empty_cwd"
    workdir.mkdir(parents=True, exist_ok=True)

    last_err = None
    for attempt in range(retries + 1):
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout,
                              env=env, cwd=workdir)
        try:
            raw = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raw = None
        if raw is not None and proc.returncode == 0 and not raw.get("is_error"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(raw))
            return _parse(raw, model, cached=False)
        last_err = (raw or {}).get("result") or proc.stderr.strip()[:500] or f"exit code {proc.returncode}"
        if raw is not None and raw.get("api_error_status") in (401, 403):
            raise RuntimeError(f"Claude CLI is not signed in: {last_err} Run `claude` in a terminal and use /login.")
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"claude -p failed after {retries + 1} tries: {last_err}")


def _parse(raw: dict, model: str, cached: bool) -> ClaudeResult:
    data = raw.get("structured_output")
    if data is None:
        text = raw.get("result", "")
        try:
            data = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            start, end = text.find("{"), text.rfind("}")
            data = json.loads(text[start : end + 1]) if start >= 0 < end else text
    return ClaudeResult(data=data, model=model, usage=raw.get("usage", {}),
                        cost_usd_equiv=raw.get("total_cost_usd"), cached=cached, raw=raw,
                        models_used=sorted(raw.get("modelUsage", {}).keys()))
