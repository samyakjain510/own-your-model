"""Freeze the test set.

Split by time: training may only use complaints received before `train_to`;
the test set is drawn from `test_from` onward, with a gap month in between so
the same burst of complaints can't land on both sides.

The test set is drawn at random from the test window, so its mix of products
matches what a deployed model would actually see. We remove:
- exact duplicates of any training-window narrative (after normalizing case/punctuation),
- exact and near-duplicates inside the test set itself (template letters).

Once written, the file's SHA-256 is recorded. Scorers refuse to run if it changes.
"""

from __future__ import annotations

import collections
import hashlib
import json
import random
from pathlib import Path

from . import pii
from .leakage import NearDupIndex, exact_hash
from .loaders.cfpb import CSV_TO_API, record_to_trace
from .schema import write_traces

MAX_WORDS = 500  # same input cap for every model, applied at prompt time


def freeze_test(corpus: str | Path, out_dir: str | Path, *, train_to: str, test_from: str, test_to: str,
                n: int, seed: int, version: str = "v1", name: str = "test",
                avoid_split: str | Path | None = None) -> dict:
    """Freeze a split. `avoid_split` is an already-frozen traces file (e.g. the dev set):
    its items, and anything near-duplicate to them, are excluded."""
    corpus, out_dir = Path(corpus), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    train_hashes: set[str] = set()
    test_pool = []
    pair_counts = collections.Counter()
    avoid_ids: set[str] = set()
    if avoid_split:
        with open(avoid_split, encoding="utf-8") as f:
            avoid_ids = {json.loads(line)["trace_id"].removeprefix("cfpb-") for line in f if line.strip()}
    avoid_texts: dict[str, str] = {}

    with open(corpus, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            d = rec["Date received"][:10]
            if d < train_to:
                train_hashes.add(exact_hash(rec["Consumer complaint narrative"]))
                pair_counts[(rec["Product"], rec["Issue"])] += 1
            elif test_from <= d <= test_to:
                if rec["Complaint ID"] in avoid_ids:
                    avoid_texts[rec["Complaint ID"]] = rec["Consumer complaint narrative"]
                else:
                    test_pool.append(rec)

    rng = random.Random(seed)
    rng.shuffle(test_pool)

    kept, kept_hashes, dropped = [], set(), collections.Counter()
    for rec in test_pool:
        if len(kept) >= n * 2:  # oversample, near-dup pass trims below
            break
        h = exact_hash(rec["Consumer complaint narrative"])
        if h in train_hashes:
            dropped["exact_dup_of_train"] += 1
            continue
        if h in kept_hashes:
            dropped["exact_dup_within_test"] += 1
            continue
        kept_hashes.add(h)
        kept.append(rec)

    # Near-duplicates inside the test set: keep the first of each cluster.
    final = []
    index = NearDupIndex(threshold=0.8)
    for aid, atxt in avoid_texts.items():  # seed with the avoided split so near-copies of it are dropped too
        index.add(f"avoid-{aid}", atxt)
    for rec in kept:
        if len(final) >= n:
            break
        cid = rec["Complaint ID"]
        txt = rec["Consumer complaint narrative"]
        hit = index.query(txt)
        if hit:
            dropped["near_dup_of_avoided_split" if str(hit[1]).startswith("avoid-") else "near_dup_within_split"] += 1
            continue
        index.add(cid, txt)
        final.append(rec)

    traces = []
    for rec in final:
        t = record_to_trace({CSV_TO_API.get(k, k): v for k, v in rec.items()})
        traces.append(pii.scrub_trace(t))

    path = out_dir / f"{name}_{version}.jsonl"
    write_traces(traces, path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()

    labels = collections.defaultdict(list)
    for (p, i), c in sorted(pair_counts.items(), key=lambda x: (x[0][0], -x[1])):
        labels[p].append(i)
    (out_dir / f"labels_{version}.json").write_text(json.dumps(labels, indent=2, ensure_ascii=False))

    manifest = {
        "version": version,
        "split": name,
        "avoided_split": str(avoid_split) if avoid_split else None,
        "n_avoided_ids": len(avoid_ids),
        "test_file": path.name,
        "test_sha256": sha,
        "n": len(traces),
        "seed": seed,
        "train_to_exclusive": train_to,
        "test_window": [test_from, test_to],
        "test_pool_size": len(test_pool),
        "dropped": dict(dropped),
        "by_product": dict(collections.Counter(t.output["product"] for t in traces).most_common()),
        "label_pairs_in_train_window": sum(len(v) for v in labels.values()),
        "max_words_at_prompt_time": MAX_WORDS,
        "corpus_sha256_note": "see data/full/narratives.stats.json",
    }
    (out_dir / f"{name}_{version}.manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


def verify_frozen(out_dir: str | Path, version: str = "v1", name: str = "test") -> Path:
    out_dir = Path(out_dir)
    m = json.loads((out_dir / f"{name}_{version}.manifest.json").read_text())
    path = out_dir / m["test_file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != m["test_sha256"]:
        raise RuntimeError(f"{path} changed since it was frozen. Refusing to score.")
    return path
