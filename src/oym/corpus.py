"""Build the working corpus from CFPB Narratives Archive ZIPs.

Streams every CSV inside every ZIP (no unzipping to disk), keeps rows that have
a narrative and fall inside the date window, and writes them as JSON lines with
the archive's own column names. Also writes counts per month and per product so
we can pick the train/test windows from evidence.
"""

from __future__ import annotations

import collections
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

csv.field_size_limit(10**8)

NARR = "Consumer complaint narrative"


def build(raw_dir: str | Path, out: str | Path, date_min: str, date_max: str) -> dict:
    raw_dir, out = Path(raw_dir), Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    zips = sorted(raw_dir.glob("*.zip"))
    per_month_all = collections.Counter()
    per_month_narr = collections.Counter()
    per_product = collections.Counter()
    seen = set()
    n_rows = n_kept = n_dup = 0
    with open(out, "w", encoding="utf-8") as fout:
        for zp in zips:
            with zipfile.ZipFile(zp) as zf:
                for member in zf.namelist():
                    if not member.lower().endswith(".csv"):
                        continue
                    with zf.open(member) as raw:
                        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
                        for row in reader:
                            n_rows += 1
                            d = (row.get("Date received") or "")[:10]
                            if not (date_min <= d <= date_max):
                                continue
                            month = d[:7]
                            per_month_all[month] += 1
                            if not (row.get(NARR) or "").strip():
                                continue
                            cid = row.get("Complaint ID")
                            if cid in seen:
                                n_dup += 1
                                continue
                            seen.add(cid)
                            per_month_narr[month] += 1
                            per_product[row.get("Product")] += 1
                            row["_source_zip"] = zp.name
                            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                            n_kept += 1
    h = hashlib.sha256(out.read_bytes()).hexdigest()
    stats = {
        "date_min": date_min,
        "date_max": date_max,
        "zips": [z.name for z in zips],
        "rows_scanned": n_rows,
        "narratives_kept": n_kept,
        "duplicate_ids_skipped": n_dup,
        "per_month": {m: {"all": per_month_all[m], "with_narrative": per_month_narr[m]} for m in sorted(per_month_all)},
        "per_product": dict(per_product.most_common()),
        "out_sha256": h,
    }
    out.with_suffix(".stats.json").write_text(json.dumps(stats, indent=2))
    return stats
