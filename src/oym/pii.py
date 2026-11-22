"""PII scrubbing.

CFPB already redacts names, dates and numbers with runs of X's ("XXXX"). Real
company logs won't be pre-scrubbed, and CFPB's own redaction can miss things,
so the kit runs its own pass on top. It replaces each hit with a typed
placeholder like [EMAIL] and records counts, so we can later measure how many
items it missed on a checked sample.

This is pattern matching only. It will miss PII that has no fixed shape (a
person's name written in a sentence, for example). The miss rate is measured,
not assumed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Order matters: more specific patterns run first.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("URL", re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.I)),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}(?!\d)")),
    ("ACCOUNT", re.compile(r"\b\d{8,}\b")),
    (
        "ADDRESS",
        re.compile(
            r"\b\d{1,6}\s+(?:[A-Z][a-z]+\s){1,3}"
            r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way)\b\.?"
        ),
    ),
]

# CFPB's own redaction marks: XXXX, XX/XX/XXXX, {$XXXX.00} etc.
CFPB_MASK = re.compile(r"\bX{2,}(?:[/-]X{2,})*\b")


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


@dataclass
class ScrubResult:
    text: str
    counts: dict[str, int]


def scrub(text: str) -> ScrubResult:
    counts: dict[str, int] = {}

    def make_sub(label):
        def _sub(m):
            s = m.group(0)
            if label == "CARD":
                digits = re.sub(r"\D", "", s)
                if not _luhn_ok(digits):
                    return s  # long number but not a card; ACCOUNT may still catch it
            counts[label] = counts.get(label, 0) + 1
            return f"[{label}]"

        return _sub

    for label, pat in PATTERNS:
        text = pat.sub(make_sub(label), text)

    n_mask = len(CFPB_MASK.findall(text))
    if n_mask:
        counts["CFPB_MASK"] = n_mask
        text = CFPB_MASK.sub("[REDACTED]", text)
    return ScrubResult(text=text, counts=counts)


def scrub_trace(trace):
    r = scrub(trace.input)
    trace.input = r.text
    trace.scrub = {"counts": r.counts, "scrubber": "regex-v1"}
    return trace
