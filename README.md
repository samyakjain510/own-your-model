# Own Your Model

**Question:** for one narrow, high-volume task, can a small open model trained on your own logs match a rented frontier model, and at what volume does owning it get cheaper?

**Answer:** not measured yet. This repo is being built in the open; every number will point to a saved run.

## Quickstart (no installs, Python 3.10+)

```bash
git clone <repo> && cd own-your-model
PYTHONPATH=src python3 -m oym quickstart
```

This turns a bundled sample of ~300 public CFPB complaints into PII-scrubbed traces in `runs/quickstart/`.

## Pipeline

```
raw logs → traces → error discovery → eval set + checked judge → training set → LoRA fine-tune → own-vs-rent cost model → decision report
```

See `docs/PLAN.md` for the plan and `docs/learn/` for plain-language notes on each step.

## Data

CFPB Consumer Complaint Database (public domain, US government). See `docs/phase0/dataset.md`.

## License

MIT.
