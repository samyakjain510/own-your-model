# Agent log

What each AI agent did, and what a human checked. This goes into the write-up.

| Date | Who | What | Human check |
|---|---|---|---|
| 2026-11-22 | Claude (lead) | Wrote plan, trace schema, CFPB loader, regex PII scrubber + 4 unit tests, CLI quickstart | none yet |
| 2026-11-22 | Research agent (Sonnet) | Competitor map, prior work, positioning note → `docs/phase0/` | none yet |
| 2026-11-22 | Research agent (Sonnet) | CFPB license/API research, fetched ~300-complaint sample, `scripts/fetch_cfpb_sample.py` | none yet |
| 2026-11-22 | Research agent (Sonnet) | Small open models, trainers, free compute, price inputs → `docs/phase0/models-compute.md` | none yet |
| 2026-11-22 | Claude (lead) | Added metrics (Wilson intervals, TPR/TNR, Cohen's kappa, bootstrap), leakage guard (exact + MinHash near-dup, refuses on overlap), `claude -p` runner with disk cache; 10 unit tests pass | none yet |
| 2026-11-22 | Claude (lead) | Style check on competitor/prior-work docs: one wording fix | none yet |
| 2026-11-22 | Research agent (Sonnet) | Models/trainers/free compute/price inputs → `docs/phase0/models-compute.md` (recommends Qwen3-4B-Instruct-2507, Granite-4.1-3B, Phi-4-mini) | none yet |
| 2026-11-22 | Claude (lead) | Claude runner: strips API keys from env (keeps $0), runs from an empty folder to avoid extra tokens | none yet |
| 2026-11-22 | Research agent (Sonnet) | Found CFPB stopped publishing narratives (Aug 2026); built 300-complaint balanced sample from CFPB Narratives Archive (July 2026 ZIP, seed 42); license notes, taxonomy dates → `docs/phase0/dataset.md` | none yet |
| 2026-11-22 | Claude (lead) | Loader maps archive column names in JSONL; quickstart runs on sample: 300 traces, 4,474 CFPB masks normalized, 0 other PII hits | none yet |
| 2026-11-22 | Claude (lead) | Found and fixed 281,839-token hidden overhead per CLI call (`--strict-mcp-config` → 902); versioned answer cache; GLM check; scope v1 written; lessons 01–02; `docs/what-went-wrong.md` started | Samyak read lesson 00 |
| 2026-11-22 | Claude (lead) | Built corpus (2,323,440 narratives, Sep 2023–Aug 2026); froze dev_v1 and test_v2 (800 each, time split, exact + near-dup removal); baseline runner + code scorer; Haiku 5.5 pilot (n=100) and prompt v1 vs v2 on dev (n=300) | none |
| 2026-11-22 | Claude (lead) | Open-coded 24 pilot misses into failure taxonomy draft 1 (`docs/phase2/failure-taxonomy.md`) | none — no human reviewed the codes |
| 2026-11-22 | Claude (lead) | Decided: publish IDs + download script, never re-host text; purged sample text from local git history; quickstart re-downloads and matched the recorded hash | Samyak delegated the decision |
| 2026-11-22 | Claude (lead) | Model-free label-noise check on exact-copy clusters; built nested train sets 500/2,000/8,000 + val 300 with majority-vote labels, dedup, decontamination; dataset card; lesson 4 | none |
