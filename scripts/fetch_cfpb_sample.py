#!/usr/bin/env python3
"""Fetch a small, reproducible sample of CFPB complaints that have narratives.

Why this reads a CSV archive and not the search API: since August 2026 the
public search API (/data-research/consumer-complaints/search/api/v1/) no
longer returns the "Consumer complaint narrative" field. CFPB moved the
previously published narratives to its FOIA Electronic Reading Room as
monthly ZIP files ("Narratives Archive"). This script downloads one such ZIP
(refusing anything over --max-mb), streams the CSV inside it, keeps rows that
have a narrative and a date >= --date-min, and draws a sample spread evenly
across products. Rows are written unmodified, with the CSV's own column names.

Standard library only.
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import random
import ssl
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

BASE = "https://files.consumerfinance.gov/f/documents/"
DEFAULT_ZIP = "CCDB_Export_20_July_2026.zip"
API_URL = ("https://www.consumerfinance.gov/data-research/consumer-complaints/"
           "search/api/v1/?size=1&no_aggs=true&has_narrative=true&sort=created_date_desc")
NARR = "Consumer complaint narrative"


def download(url, dest, max_bytes, cafile=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; own-your-model-research)", "Accept": "*/*"})
    ctx = ssl.create_default_context(cafile=cafile)
    for attempt in range(4):  # the CDN sometimes answers 403 once, then 200
        try:
            r = urllib.request.urlopen(req, timeout=120, context=ctx)
            break
        except urllib.error.HTTPError as e:
            if e.code != 403 or attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    with r:
        size = int(r.headers.get("Content-Length", "0"))
        if size > max_bytes:
            raise SystemExit(f"{url} is {size} bytes, over the {max_bytes} limit")
        got = 0
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                got += len(chunk)
                if got > max_bytes:
                    raise SystemExit("download exceeded size limit")
                f.write(chunk)
    return got


def spread(by_product, n, rng):
    """Equal share per product; leftover slots go to products that still have rows."""
    pools = {p: rng.sample(rows, len(rows)) for p, rows in sorted(by_product.items())}
    out, taken = [], {p: 0 for p in pools}
    while len(out) < n and any(taken[p] < len(pools[p]) for p in pools):
        for p in pools:
            if len(out) >= n:
                break
            if taken[p] < len(pools[p]):
                out.append(pools[p][taken[p]])
                taken[p] += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out", default="data/sample/cfpb_sample.jsonl")
    ap.add_argument("--date-min", default="2026-07-01", help="YYYY-MM-DD, on 'Date received'")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--zip-name", default=DEFAULT_ZIP, help="file name under " + BASE)
    ap.add_argument("--cafile", default=None, help="CA bundle, e.g. /etc/ssl/cert.pem on a macOS python.org build")
    ap.add_argument("--max-mb", type=int, default=50)
    a = ap.parse_args()

    url = BASE + a.zip_name
    csv.field_size_limit(10 ** 9)
    with tempfile.TemporaryDirectory() as tmp:
        zpath = os.path.join(tmp, "archive.zip")
        nbytes = download(url, zpath, a.max_mb * 1024 * 1024, a.cafile)
        by_product, seen = {}, 0
        with zipfile.ZipFile(zpath) as z:
            name = z.namelist()[0]
            with io.TextIOWrapper(z.open(name), encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    seen += 1
                    if row[NARR].strip() and row["Date received"] >= a.date_min:
                        by_product.setdefault(row["Product"], []).append(row)
    rng = random.Random(a.seed)
    rows = spread(by_product, a.n, rng)
    rows.sort(key=lambda r: int(r["Complaint ID"]))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    sha = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
    counts = {}
    for r in rows:
        counts[r["Product"]] = counts.get(r["Product"], 0) + 1
    meta = {
        "date_fetched": datetime.date.today().isoformat(),
        "source_url": url,
        "source_zip_bytes": nbytes,
        "source_csv_name": name,
        "source_csv_rows_scanned": seen,
        "rows_with_narrative_and_date_ok": sum(len(v) for v in by_product.values()),
        "filters": {"date_received_min": a.date_min, "narrative_not_empty": True},
        "sampling": "equal share per product, then fill leftovers; random.Random(seed)",
        "seed": a.seed,
        "n_requested": a.n,
        "count": len(rows),
        "product_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
        "api_probe_url": API_URL,
        "api_probe_result": "HTTP 200 but records carry no narrative field and has_narrative is ignored (checked 2026-11-22)",
        "sha256": sha,
        "out": a.out,
    }
    with open(a.out.replace(".jsonl", ".meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    print(json.dumps(meta["product_counts"], indent=2), len(rows))


if __name__ == "__main__":
    main()
