"""Command line entry point: `python -m oym <command>`."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from . import pii
from .loaders import cfpb
from .schema import read_traces, write_traces

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "data" / "sample" / "cfpb_sample.jsonl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_traces(args) -> int:
    src = Path(args.input)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    traces = cfpb.load(src)
    if not args.no_scrub:
        traces = (pii.scrub_trace(t) for t in traces)
    n = write_traces(traces, out)

    by_product = collections.Counter()
    scrub_totals = collections.Counter()
    for t in read_traces(out):
        by_product[t.output.get("product")] += 1
        scrub_totals.update(t.scrub.get("counts", {}))

    manifest = {
        "command": "traces",
        "input": str(src),
        "input_sha256": sha256_file(src),
        "output": str(out),
        "output_sha256": sha256_file(out),
        "n_traces": n,
        "by_product": dict(by_product.most_common()),
        "scrub_counts": dict(scrub_totals),
    }
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Wrote {n} traces to {out}")
    print("Traces per product (consumer-selected label):")
    for p, c in by_product.most_common():
        print(f"  {c:5d}  {p}")
    print("PII placeholders inserted:", dict(scrub_totals) or "none")
    return 0


def ensure_sample() -> bool:
    """Download the sample from CFPB on first run (we never re-host complaint text), then
    check it byte-for-byte against the SHA-256 recorded when the sample was first drawn."""
    meta_path = SAMPLE.with_suffix(".meta.json")
    if not SAMPLE.exists():
        print("Downloading the sample from CFPB's Narratives Archive (about 17 MB, one time)...")
        cmd = [sys.executable, str(ROOT / "scripts" / "fetch_cfpb_sample.py"), "--out", str(SAMPLE)]
        if Path("/etc/ssl/cert.pem").exists():
            cmd += ["--cafile", "/etc/ssl/cert.pem"]
        meta_backup = meta_path.read_text() if meta_path.exists() else None
        if subprocess.run(cmd, cwd=ROOT).returncode != 0:
            print("Download failed. See scripts/fetch_cfpb_sample.py --help.", file=sys.stderr)
            return False
        if meta_backup is not None:  # keep the original recorded hash for the check below
            meta_path.write_text(meta_backup)
    if meta_path.exists():
        expected = json.loads(meta_path.read_text()).get("sha256")
        if expected and sha256_file(SAMPLE) != expected:
            print(f"Warning: sample hash differs from the recorded one ({expected[:12]}...). "
                  "CFPB may have changed the archive file.", file=sys.stderr)
    return True


def cmd_quickstart(args) -> int:
    if not ensure_sample():
        return 1
    args.input = str(SAMPLE)
    args.out = str(ROOT / "runs" / "quickstart" / "traces.jsonl")
    args.no_scrub = False
    return cmd_traces(args)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="oym", description="Own Your Model: workflow logs to an own-vs-rent decision.")
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("quickstart", help="Run the pipeline on the bundled tiny sample.")
    q.set_defaults(func=cmd_quickstart)

    t = sub.add_parser("traces", help="Turn raw logs into scrubbed traces.")
    t.add_argument("input", help="CFPB API JSONL or CSV export")
    t.add_argument("--out", required=True)
    t.add_argument("--no-scrub", action="store_true")
    t.set_defaults(func=cmd_traces)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
