"""Loader for the CFPB Consumer Complaint Database.

Accepts either the search API's JSON records (one per line, optionally wrapped
in Elasticsearch's {"_source": {...}}) or the official CSV export. Rows without
a narrative are skipped, since there is nothing for a model to read.

The product/issue labels in this data were picked by the consumer when filing,
so we record them with output_origin="consumer_selected". They are human labels,
but noisy ones, and the error-discovery step treats them that way.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Iterator

from ..schema import Trace

# CSV header -> API field name
CSV_TO_API = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "complaint_what_happened",
    "Company public response": "company_public_response",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Tags": "tags",
    "Consumer consent provided?": "consumer_consent_provided",
    "Submitted via": "submitted_via",
    "Date sent to company": "date_sent_to_company",
    "Company response to consumer": "company_response",
    "Timely response?": "timely",
    "Consumer disputed?": "consumer_disputed",
    "Complaint ID": "complaint_id",
}

_WS = re.compile(r"[ \t]+")


def _clean(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def _normalize_text(text: str) -> str:
    lines = [_WS.sub(" ", ln).strip() for ln in text.replace("\r\n", "\n").split("\n")]
    out, blank = [], False
    for ln in lines:
        if not ln:
            if not blank and out:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip()


def _iter_raw(path: Path) -> Iterator[dict]:
    if path.suffix.lower() == ".csv":
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                yield {CSV_TO_API.get(k, k): v for k, v in row.items()}
    else:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    yield rec.get("_source", rec)


def record_to_trace(rec: dict) -> Trace | None:
    narrative = _clean(rec.get("complaint_what_happened"))
    if not narrative:
        return None
    date = _clean(rec.get("date_received")) or ""
    return Trace(
        trace_id=f"cfpb-{rec.get('complaint_id')}",
        source="cfpb",
        input=_normalize_text(narrative),
        # Known at intake: when and how it arrived, and the consumer's state/tags.
        context={
            "date_received": date[:10] or None,
            "submitted_via": _clean(rec.get("submitted_via")),
            "state": _clean(rec.get("state")),
            "tags": _clean(rec.get("tags")),
        },
        # The routing decision recorded in the log.
        output={
            "product": _clean(rec.get("product")),
            "sub_product": _clean(rec.get("sub_product")),
            "issue": _clean(rec.get("issue")),
            "sub_issue": _clean(rec.get("sub_issue")),
        },
        output_origin="consumer_selected",
        # Known only later. Kept out of model inputs to avoid leaking the answer.
        metadata={
            "company": _clean(rec.get("company")),
            "company_response": _clean(rec.get("company_response")),
            "company_public_response": _clean(rec.get("company_public_response")),
            "timely": _clean(rec.get("timely")),
            "consumer_disputed": _clean(rec.get("consumer_disputed")),
            "date_sent_to_company": _clean(rec.get("date_sent_to_company")),
        },
    )


def load(path: str | Path) -> Iterator[Trace]:
    seen = set()
    for rec in _iter_raw(Path(path)):
        t = record_to_trace(rec)
        if t is None or t.trace_id in seen:
            continue
        seen.add(t.trace_id)
        yield t
