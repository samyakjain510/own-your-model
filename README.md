# Own Your Model

**Question:** for one narrow, high-volume task, can a small open model trained on your own logs match a rented frontier model, and at what volume does owning it get cheaper?

**Answer, for one job (routing consumer-finance complaints to one of 138 product-issue labels):** yes on quality, and owning gets cheaper only if you'd otherwise rent a big model.

- Qwen3-4B, trained with LoRA on 8,000 logged complaints on a free GPU, routed 51.4% of 800 sealed test complaints to the exact product and issue. Claude Haiku 5.5 got 42.4% and Claude Sonnet 5.5 got 48.9%. The gap over Haiku is +9.0 points (95% interval +5.6 to +12.5); against Sonnet it's level.
- Per 1,000 complaints: Haiku with batch pricing $0.080, Sonnet with batch pricing $0.96, the trained model on one rented T4 GPU $0.102.
- Owning beats renting Sonnet from about 3.5 million complaints a month, counting an assumed $2,833 a month of people time. It never beats Haiku on price at the speed we measured.

Every number points to a saved run: `runs/final/summary.json` and `docs/learn/09-final-results.md`. Choices were locked before the test set was opened: `docs/phase4/locked-choices.md`.

## Quickstart (no installs, Python 3.10+)

```bash
git clone https://github.com/samyakjain510/own-your-model.git && cd own-your-model
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
