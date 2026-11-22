"""The common trace schema.

A "trace" is one unit of work from a workflow log: what came in, what context
the worker had, and what decision came out. Every loader turns its raw source
into this shape so the rest of the kit never has to know where data came from.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "1"


@dataclass
class Trace:
    trace_id: str
    source: str  # e.g. "cfpb"
    input: str  # the text the worker read (PII-scrubbed after the scrub step)
    context: dict[str, Any] = field(default_factory=dict)  # facts known at intake time
    output: dict[str, Any] = field(default_factory=dict)  # the decision recorded in the log
    output_origin: str = "unknown"  # who made the logged decision, e.g. "consumer_selected"
    metadata: dict[str, Any] = field(default_factory=dict)  # facts known only later (outcomes)
    scrub: dict[str, Any] = field(default_factory=dict)  # what the PII step changed
    schema_version: str = SCHEMA_VERSION

    @property
    def input_hash(self) -> str:
        """Hash of the normalized input text. Used for de-duplication and leakage checks."""
        norm = " ".join(self.input.lower().split())
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]

    def to_json(self) -> str:
        d = asdict(self)
        d["input_hash"] = self.input_hash
        return json.dumps(d, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> "Trace":
        d = json.loads(line)
        d.pop("input_hash", None)
        return cls(**d)


def write_traces(traces, path) -> int:
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for t in traces:
            f.write(t.to_json() + "\n")
            n += 1
    return n


def read_traces(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield Trace.from_json(line)
