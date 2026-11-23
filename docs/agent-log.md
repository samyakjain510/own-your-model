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
| 2026-11-22 | Claude (lead) | Set up Kaggle CLI with Samyak's token (he placed it); uploaded private dataset `oym-cfpb-routing-v1` (train sets, val, dev prompts; no test set); wrote Unsloth train+eval script; pushed private smoke run on T4 | Samyak created the Kaggle account and token |
| 2026-11-22 | Claude (lead) | Kaggle smoke run passed end to end (T4, peak 8.6 GB); fixed think-block template quirk; pushed full runs A (zero-shot + 500 + 2,000) and B (8,000) in parallel | none |
| 2026-11-22 | Claude (lead) | Cost model (`src/oym/cost.py`, `configs/cost_inputs.json`): four options, idle GPU time, engineering line (assumption), break-even search; dry run on smoke numbers saved as preliminary | none |
| 2026-11-22 | Claude (lead) | Job A finished (zero-shot, 500, 2,000); scored on dev 800; paired comparison vs Haiku on the shared 300 (`src/oym/compare.py`); lesson 6 draft; fixed config-injection crash in the speed-test job and re-pushed | none |
| 2026-11-22 | Claude (lead) | Found Haiku thinks on 23/30 calls; measured Haiku at low effort on dev 300 (no thinking: product-and-issue drops 12 points); cost model now prices Claude as a well-built API setup; 3 cost tests | none |
| 2026-11-22 | Claude (lead) | Planted-PII check (fake values only, no hand labels): measured scrubber v1 misses, wrote v2, re-measured on fresh values plus a false-alarm check; 2 new tests | none |
| 2026-11-22 | Claude (lead) | Label checker (`src/oym/audit.py`): planted-error calibration, split audit, audited scoring; 10-item Opus trial ran; the 400-item calibration stopped at the subscription's 5-hour limit (answers that finished are cached and will be reused on rerun) | none |
| 2026-11-23 | Claude (lead) | Scored 8,000-example run; label-checker calibration finished (Opus 5.5, 400 dev, planted errors); issue-level miss counts; lessons 6–7; split speed tests into separate HF and vLLM jobs | none — no human reviewed the checker's flags |
| 2026-11-23 | Claude (lead) | Audited dev scores (checker on dev 300); speed tests (HF 2.40/s, vLLM 2.02/s on T4); added T4 price (AWS g4dn.xlarge, $0.526/h, via web-fetch agent); cost report v1 on dev numbers; lesson 8 | none |
| 2026-11-23 | Claude (lead) | Tried worked examples for Haiku on dev (not chosen); locked all choices; opened test_v2: small models on Kaggle, Haiku, Sonnet and the Opus checker through the subscription; final scoring (`scripts/final_report.py`); lesson 9; README answer; found and fixed the prompt-cutting bug | none — Samyak hasn't reviewed the final results yet |
