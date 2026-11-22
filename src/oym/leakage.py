"""Train/test leakage guard.

If a test item (or a near copy of it) is also in the training data, the test
score is inflated and means nothing. Complaint data has lots of near copies:
template letters, the same person filing twice. This module finds exact and
near-duplicate overlap and refuses to continue if any is found.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict

_TOKEN = re.compile(r"[a-z0-9]+")


class LeakageError(RuntimeError):
    pass


def normalize(text: str) -> str:
    return " ".join(_TOKEN.findall(text.lower()))


def exact_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode()).hexdigest()[:16]


def shingles(text: str, k: int = 5) -> set[str]:
    toks = normalize(text).split()
    if len(toks) < k:
        return {" ".join(toks)} if toks else set()
    return {" ".join(toks[i : i + k]) for i in range(len(toks) - k + 1)}


def _minhash(sh: set[str], num_perm: int = 64) -> tuple[int, ...]:
    if not sh:
        return tuple([0] * num_perm)
    sig = []
    for i in range(num_perm):
        salt = i.to_bytes(2, "big")
        sig.append(min(int.from_bytes(hashlib.blake2b(salt + s.encode(), digest_size=8).digest(), "big") for s in sh))
    return tuple(sig)


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a or b else 0.0


def find_overlap(train_texts: dict[str, str], test_texts: dict[str, str], threshold: float = 0.8,
                 num_perm: int = 64, bands: int = 16) -> list[dict]:
    """Return test items that match a training item exactly or with Jaccard >= threshold.

    Uses MinHash + banding to find candidate pairs, then checks real Jaccard on
    the candidates. Inputs map item id -> text.
    """
    rows = num_perm // bands
    hits = []

    train_exact = defaultdict(list)
    for tid, txt in train_texts.items():
        train_exact[exact_hash(txt)].append(tid)

    train_sh = {tid: shingles(txt) for tid, txt in train_texts.items()}
    buckets = defaultdict(set)
    for tid, sh in train_sh.items():
        sig = _minhash(sh, num_perm)
        for b in range(bands):
            buckets[(b, sig[b * rows : (b + 1) * rows])].add(tid)

    for qid, txt in test_texts.items():
        ex = train_exact.get(exact_hash(txt))
        if ex:
            hits.append({"test_id": qid, "train_id": ex[0], "kind": "exact", "jaccard": 1.0})
            continue
        sh = shingles(txt)
        sig = _minhash(sh, num_perm)
        cands = set()
        for b in range(bands):
            cands |= buckets.get((b, sig[b * rows : (b + 1) * rows]), set())
        best = max(((jaccard(sh, train_sh[c]), c) for c in cands), default=(0.0, None))
        if best[0] >= threshold:
            hits.append({"test_id": qid, "train_id": best[1], "kind": "near", "jaccard": round(best[0], 3)})
    return hits


def assert_no_leakage(train_texts: dict[str, str], test_texts: dict[str, str], threshold: float = 0.8) -> None:
    hits = find_overlap(train_texts, test_texts, threshold)
    if hits:
        sample = ", ".join(f"{h['test_id']}~{h['train_id']}({h['kind']})" for h in hits[:5])
        raise LeakageError(f"{len(hits)} test items overlap training data: {sample}. Remove them before scoring.")
