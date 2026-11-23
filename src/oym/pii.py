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
# v1: the first version. Kept so its measured miss rate stays reproducible.
PATTERNS_V1: list[tuple[str, re.Pattern]] = [
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

# v2: fixes the formats v1 missed in the planted-PII check (src/oym/pii_eval.py):
# SSNs with spaces, account numbers with letters or dashes, addresses with a
# direction letter or in lowercase. Street-name words can't be filler words, so
# "paid 300 to the court" isn't taken for an address.
_FILLER = r"(?:to|the|on|of|in|a|an|my|by|for|and|at|is|was|were|be|their|this|that|per|from|with|it|no|or|we|i)"
PATTERNS: list[tuple[str, re.Pattern]] = [
    PATTERNS_V1[0],
    PATTERNS_V1[1],
    ("SSN", re.compile(r"\b\d{3}[- ]\d{2}[- ]\d{4}\b")),
    PATTERNS_V1[3],
    PATTERNS_V1[4],
    ("ACCOUNT", re.compile(r"\b[A-Za-z]{1,4}-?\d{6,}\b|(?<![\d-])(?!\d{4}-\d{2}-\d{2}(?![\d-]))\d{2,6}(?:-\d{2,6}){1,4}(?![\d-])|\b\d{8,}\b")),
    (
        "ADDRESS",
        re.compile(
            r"\b\d{1,6}\s+(?:(?:N|S|E|W|NE|NW|SE|SW)\.?\s+)?(?:(?!" + _FILLER + r"\b)[A-Za-z]+\s){1,3}"
            r"(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|way)\b\.?",
            re.I,
        ),
    ),
]
SCRUBBERS = {"regex-v1": PATTERNS_V1, "regex-v2": PATTERNS}
DEFAULT_SCRUBBER = "regex-v2"

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


def scrub(text: str, scrubber: str = DEFAULT_SCRUBBER) -> ScrubResult:
    counts: dict[str, int] = {}

    def make_sub(label):
        def _sub(m):
            s = m.group(0)
            if label == "CARD":
                digits = re.sub(r"\D", "", s)
                if not _luhn_ok(digits):
                    return s  # long number but not a card; ACCOUNT may still catch it
            if label == "ACCOUNT" and "-" in s and s[0].isdigit() and len(re.sub(r"\D", "", s)) < 8:
                return s  # short dashed numbers are usually dates or reference codes
            counts[label] = counts.get(label, 0) + 1
            return f"[{label}]"

        return _sub

    for label, pat in SCRUBBERS[scrubber]:
        text = pat.sub(make_sub(label), text)

    n_mask = len(CFPB_MASK.findall(text))
    if n_mask:
        counts["CFPB_MASK"] = n_mask
        text = CFPB_MASK.sub("[REDACTED]", text)
    return ScrubResult(text=text, counts=counts)


def scrub_trace(trace):
    r = scrub(trace.input)
    trace.input = r.text
    trace.scrub = {"counts": r.counts, "scrubber": DEFAULT_SCRUBBER}
    return trace
