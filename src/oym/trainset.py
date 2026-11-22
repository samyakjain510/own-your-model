"""Build training sets from the logs.

Steps, in order:
1. Take complaints from the training window only (before the test gap).
2. Collapse exact copies (same normalized text) into one example. Its label is
   the most common label among the copies, so one template letter filed 500
   times counts once, and copies vote on the label.
3. Drop anything that is an exact or near copy of a dev or test complaint
   (decontamination), and near copies of examples already kept (dedup).
4. Shuffle with a fixed seed and take nested sets: the 500 set is inside the
   2,000 set, which is inside the 8,000 set. A separate validation set comes
   from the same pool, for watching training loss only.
5. Scrub PII and write chat-format JSONL that MLX-LM, Unsloth and TRL all read.

The small model's prompt is short: no label list, because it learns the labels
from the examples. That keeps inference cheap.
"""

from __future__ import annotations

import collections
import hashlib
import json
import random
from pathlib import Path

from . import pii
from .baseline import truncate
from .leakage import NearDupIndex, exact_hash, find_overlap
from .loaders.cfpb import CSV_TO_API, record_to_trace

SYSTEM = ("Route this consumer finance complaint. Reply with JSON: "
          '{"product": "...", "issue": "..."} using the CFPB product and issue names.')


def user_text(company: str | None, narrative: str) -> str:
    return f"Company: {company or 'unknown'}\n\nComplaint:\n{truncate(narrative)}"


def to_chat(trace) -> dict:
    target = json.dumps({"product": trace.output["product"], "issue": trace.output["issue"]}, ensure_ascii=False)
    return {"messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_text(trace.context.get("company"), trace.input)},
        {"role": "assistant", "content": target},
    ], "trace_id": trace.trace_id}


def _ids(path: Path) -> set[str]:
    return {line.strip().removeprefix("cfpb-") for line in open(path) if line.strip()}


def build(corpus: str | Path, out_dir: str | Path, *, date_from: str, date_to: str, sizes=(500, 2000, 8000),
          n_val: int = 300, seed: int = 7, avoid_id_files=()) -> dict:
    corpus, out_dir = Path(corpus), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    avoid_ids = set().union(*[_ids(Path(p)) for p in avoid_id_files]) if avoid_id_files else set()

    clusters: dict[str, list[dict]] = collections.defaultdict(list)
    avoid_texts: dict[str, str] = {}
    n_window = 0
    with open(corpus, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["Complaint ID"] in avoid_ids:
                avoid_texts[r["Complaint ID"]] = r["Consumer complaint narrative"]
                continue
            d = r["Date received"][:10]
            if date_from <= d <= date_to:
                n_window += 1
                clusters[exact_hash(r["Consumer complaint narrative"])].append(r)
    avoid_hashes = {exact_hash(t) for t in avoid_texts.values()}

    # One example per exact-copy cluster, labeled by majority vote of the copies.
    reps, relabeled = [], 0
    for h, rows in clusters.items():
        if h in avoid_hashes:
            continue
        votes = collections.Counter((r["Product"], r["Issue"]) for r in rows)
        (prod, iss), _ = votes.most_common(1)[0]
        rep = dict(sorted(rows, key=lambda r: r["Date received"])[-1])  # most recent copy as the text source
        if (rep["Product"], rep["Issue"]) != (prod, iss):
            relabeled += 1
        rep["Product"], rep["Issue"] = prod, iss
        rep["_copies"] = len(rows)
        reps.append(rep)
    reps.sort(key=lambda r: r["Complaint ID"])  # deterministic order before shuffling
    random.Random(seed).shuffle(reps)

    need = max(sizes) + n_val
    index = NearDupIndex(threshold=0.8)
    for aid, txt in avoid_texts.items():
        index.add(f"avoid-{aid}", txt)
    kept, dropped = [], collections.Counter()
    for r in reps:
        if len(kept) >= need:
            break
        hit = index.query(r["Consumer complaint narrative"])
        if hit:
            dropped["near_copy_of_dev_or_test" if str(hit[1]).startswith("avoid-") else "near_copy_within_train"] += 1
            continue
        index.add(r["Complaint ID"], r["Consumer complaint narrative"])
        kept.append(r)

    traces = [pii.scrub_trace(record_to_trace({CSV_TO_API.get(k, k): v for k, v in r.items()})) for r in kept]
    val, train = traces[:n_val], traces[n_val:]

    # Independent second check: banded MinHash overlap between the final training pool and dev+test.
    overlap = find_overlap({r["Complaint ID"]: r["Consumer complaint narrative"] for r in kept}, avoid_texts)
    if overlap:
        raise RuntimeError(f"Leakage check failed after decontamination: {overlap[:3]}")

    files = {}
    for name, items in [("val", val)] + [(f"train_{n}", train[:n]) for n in sorted(sizes)]:
        path = out_dir / f"{name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for t in items:
                f.write(json.dumps(to_chat(t), ensure_ascii=False) + "\n")
        files[name] = {"n": len(items), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                       "by_product": dict(collections.Counter(t.output["product"] for t in items).most_common())}
        (out_dir / f"{name}.ids.txt").write_text("\n".join(t.trace_id for t in items) + "\n")

    manifest = {
        "window": [date_from, date_to],
        "seed": seed,
        "complaints_in_window": n_window,
        "exact_copy_clusters": len(clusters),
        "clusters_matching_dev_or_test_text": sum(1 for h in clusters if h in avoid_hashes),
        "clusters_whose_label_changed_by_majority_vote": relabeled,
        "dropped_while_sampling": dict(dropped),
        "leakage_check": "passed (exact + MinHash near-dup, Jaccard >= 0.8, vs dev_v1 and test_v2)",
        "avoided_items": len(avoid_texts),
        "system_prompt": SYSTEM,
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest
