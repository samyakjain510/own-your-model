"""Measure the PII scrubber's miss rate by planting fake PII into real complaints.

Nobody hand-labels anything here. We generate fake emails, phone numbers, SSNs,
card numbers, account numbers, street addresses, links and names in the
formats people actually type, plant one into a complaint, scrub it, and check
whether any identifying piece of it survived. All values are synthetic.

A planted value counts as caught only if every identifying fragment of it
(for example each run of 3+ digits) is gone. We compare against the scrubbed
original so a fragment that was already in the complaint doesn't count as a leak.

  PYTHONPATH=src python -m oym.pii_eval data/sample/cfpb_sample.jsonl runs/pii
"""

from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .metrics import wilson
from .pii import scrub
from .loaders.cfpb import load

FIRST = ["Maria", "James", "Aisha", "Wei", "Carlos", "Emily", "Darnell", "Priya", "Olga", "Tom"]
LAST = ["Gonzalez", "Whitfield", "Okafor", "Nakamura", "Brennan", "Lindqvist", "Patel", "Moreau", "Kowalski", "Haddad"]
STREETS = ["Maple", "Oak", "Cedar Ridge", "Washington", "Lakeview", "Elm", "Pine Hollow", "Main"]
SUFFIX = ["Street", "St", "Avenue", "Ave", "Road", "Rd", "Drive", "Dr", "Lane", "Blvd", "Court", "Way"]
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "aol.com", "comcast.net"]


def _luhn_complete(prefix: str, length: int, rng: random.Random) -> str:
    body = prefix + "".join(str(rng.randrange(10)) for _ in range(length - len(prefix) - 1))
    for check in range(10):
        digits = body + str(check)
        total, alt = 0, False
        for ch in reversed(digits):
            d = int(ch) * (2 if alt else 1)
            total += d - 9 if d > 9 else d
            alt = not alt
        if total % 10 == 0:
            return digits
    raise AssertionError


def _d(rng, n):
    return "".join(str(rng.randrange(10)) for _ in range(n))


# Each generator returns (variant name, value, sentence template). Variants cover how people really write.
def gen_email(rng):
    f, l = rng.choice(FIRST).lower(), rng.choice(LAST).lower()
    local = rng.choice([f"{f}.{l}", f"{f[0]}{l}{rng.randrange(10, 99)}", f"{f}_{l}"])
    return "standard", f"{local}@{rng.choice(DOMAINS)}", "Please email me at {v} with an update."


def gen_phone(rng):
    a, b, c = str(rng.randrange(201, 989)), _d(rng, 3), _d(rng, 4)
    variant, v = rng.choice([("(xxx) xxx-xxxx", f"({a}) {b}-{c}"), ("xxx-xxx-xxxx", f"{a}-{b}-{c}"),
                             ("xxx.xxx.xxxx", f"{a}.{b}.{c}"), ("+1 xxx xxx xxxx", f"+1 {a} {b} {c}"),
                             ("10 digits", f"{a}{b}{c}")])
    return variant, v, "You can call me at {v} any time."


def gen_ssn(rng):
    a, b, c = str(rng.randrange(100, 899)), _d(rng, 2), _d(rng, 4)
    variant, v = rng.choice([("xxx-xx-xxxx", f"{a}-{b}-{c}"), ("xxx xx xxxx", f"{a} {b} {c}"),
                             ("9 digits", f"{a}{b}{c}")])
    return variant, v, "My social security number is {v} and it was used without my consent."


def gen_card(rng):
    variant = rng.choice(["16 digits", "16 with spaces", "16 with dashes", "Amex 15"])
    if variant == "Amex 15":
        return variant, _luhn_complete("37", 15, rng), "The charge was on my card {v} last month."
    n = _luhn_complete(rng.choice(["4", "51", "55"]), 16, rng)
    sep = {"16 digits": "", "16 with spaces": " ", "16 with dashes": "-"}[variant]
    return variant, sep.join(n[i : i + 4] for i in range(0, 16, 4)), "The charge was on my card {v} last month."


def gen_account(rng):
    variant, v = rng.choice([("8-12 digits", _d(rng, rng.randrange(8, 13))),
                             ("letters + digits", f"{rng.choice(['AC', 'LN', 'CK'])}{_d(rng, 8)}"),
                             ("with dashes", f"{_d(rng, 4)}-{_d(rng, 4)}-{_d(rng, 2)}")])
    return variant, v, "My account number is {v} at this bank."


def gen_address(rng):
    num, street, suf = str(rng.randrange(1, 9999)), rng.choice(STREETS), rng.choice(SUFFIX)
    variant, v = rng.choice([("123 Maple Street", f"{num} {street} {suf}"),
                             ("123 N Maple St", f"{num} {rng.choice('NSEW')} {street} {suf}"),
                             ("lowercase", f"{num} {street.lower()} {suf.lower()}"),
                             ("with apt", f"{num} {street} {suf} Apt {rng.randrange(1, 40)}")])
    return variant, v, "They sent the letter to {v} even though I moved."


def gen_url(rng):
    # A bare company domain ("smithpay.com") was in the first run; it was dropped because
    # a company's web address isn't personal data. Links can carry personal IDs, so those stay.
    variant, v = rng.choice([("https", f"https://www.{rng.choice(LAST).lower()}bank.com/login?id={_d(rng, 6)}"),
                             ("www", f"www.{rng.choice(LAST).lower()}-collections.com/acct/{_d(rng, 5)}")])
    return variant, v, "I found their notice at {v} after searching."


def gen_name(rng):
    return "full name", f"{rng.choice(FIRST)} {rng.choice(LAST)}", "The agent I spoke with, {v}, hung up on me."


GENERATORS = {"EMAIL": gen_email, "PHONE": gen_phone, "SSN": gen_ssn, "CARD": gen_card, "ACCOUNT": gen_account,
              "ADDRESS": gen_address, "URL": gen_url, "NAME": gen_name}


def fragments(kind: str, value: str) -> list[str]:
    """Pieces of the value that would still identify someone if left in the text."""
    frags = re.findall(r"\d{3,}", value)
    if kind == "EMAIL":
        frags.append(value.split("@")[0])
    elif kind == "URL":
        frags.append(re.sub(r"^(https?://)?(www\.)?", "", value).split("/")[0])
    elif kind == "NAME":
        frags.append(value.split()[-1])
    elif kind == "ADDRESS":
        frags.append(value.split()[0] + " ")
    elif kind == "ACCOUNT" and not frags:
        frags.append(value)
    return frags or [value]


def plant(text: str, sentence: str, rng: random.Random) -> str:
    cuts = [m.end() for m in re.finditer(r"[.!?]\s+", text)]
    at = rng.choice(cuts) if cuts else len(text)
    return text[:at] + sentence + " " + text[at:]


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October"]


def demask(text: str, rng: random.Random) -> str:
    """Swap CFPB's date masks and some XXXX masks for realistic numbers that are NOT personal data
    (dates, amounts, times, years, durations), the kind real company logs are full of."""
    def date(_):
        m, d, y = rng.randrange(1, 13), rng.randrange(1, 29), rng.randrange(2019, 2027)
        return rng.choice([f"{m:02d}/{d:02d}/{y}", f"{y}-{m:02d}-{d:02d}", f"{MONTHS[m % 10]} {d}, {y}"])

    def other(_):
        return rng.choice([f"${rng.randrange(10, 9999):,}.{_d(rng, 2)}", str(rng.randrange(2015, 2027)),
                           f"{rng.randrange(1, 12)}:{_d(rng, 2)} PM", f"{rng.randrange(2, 90)} days",
                           f"{rng.randrange(1, 9)} of {rng.randrange(10, 30)} payments", "XXXX"])

    text = re.sub(r"XX/XX/X{2,4}", date, text)
    return re.sub(r"\bX{4}\b", other, text)


def evaluate(sample_path: str | Path, out_dir: str | Path, per_type: int = 200, seed: int = 8,
             scrubber: str = "regex-v2") -> dict:
    rng = random.Random(seed)
    texts = [t.input for t in load(sample_path)]
    caught, total = Counter(), Counter()
    by_variant = defaultdict(lambda: [0, 0])
    misses = defaultdict(list)
    for kind, gen in GENERATORS.items():
        for _ in range(per_type):
            base = rng.choice(texts)
            variant, value, tpl = gen(rng)
            planted = plant(base, tpl.format(v=value), rng)
            before, after = scrub(base, scrubber).text, scrub(planted, scrubber).text
            leaked = [f for f in fragments(kind, value) if after.count(f) > before.count(f)]
            total[kind] += 1
            by_variant[(kind, variant)][1] += 1
            if not leaked:
                caught[kind] += 1
                by_variant[(kind, variant)][0] += 1
            elif len(misses[kind]) < 5:
                misses[kind].append({"variant": variant, "value": value, "leaked": leaked})

    # False alarms: anything tagged in complaints whose masks were swapped for non-personal numbers.
    tags, alarm_examples = Counter(), []
    for t in texts:
        dm = demask(t, rng)
        r = scrub(dm, scrubber)
        for k, n in r.counts.items():
            if k != "CFPB_MASK":
                tags[k] += n
                if len(alarm_examples) < 8:
                    i = r.text.find(f"[{k}]")
                    alarm_examples.append(r.text[max(0, i - 50) : i + 30])

    result = {
        "sample": str(sample_path), "complaints": len(texts), "planted_per_type": per_type, "seed": seed,
        "scrubber": scrubber,
        "catch_rate": {k: str(wilson(caught[k], total[k])) for k in GENERATORS},
        "catch_rate_by_variant": {f"{k} / {v}": f"{c}/{n}" for (k, v), (c, n) in sorted(by_variant.items())},
        "example_misses": dict(misses),
        "false_alarms_on_demasked_complaints": {"tags": dict(tags), "per_1000_complaints": round(
            1000 * sum(tags.values()) / len(texts), 1), "examples": alarm_examples},
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"pii_eval_{scrubber}_seed{seed}.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    for name in ("regex-v1", "regex-v2"):
        r = evaluate(sys.argv[1], sys.argv[2], scrubber=name)
        print(name, json.dumps(r["catch_rate"], indent=1), r["false_alarms_on_demasked_complaints"])
