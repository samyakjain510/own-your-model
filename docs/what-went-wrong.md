# What went wrong (and what changed)

A running list for the write-up. Each entry: what happened, the evidence, and what we changed.

1. **CFPB stopped publishing complaint text (found 2026-11-22).** The live API dropped narratives in Sept 2026. Evidence: `docs/phase0/dataset.md`. Change: text now comes from CFPB's Narratives Archive ZIPs; the data window ends Aug 14, 2026; we plan to share complaint IDs plus a download script rather than re-hosting text.
2. **Every Claude call carried 281,839 hidden prompt tokens (found 2026-11-22).** The CLI loaded all of the user's connected apps as tools. Evidence: usage JSON from the first test call. Change: `--strict-mcp-config` in `src/oym/claude_cli.py`; the same call dropped to 902 tokens. The cache key now includes a runner version so stale measurements aren't reused.
3. **Claude answered with a retired category name (found 2026-11-22).** Asked for a product with no label list, Haiku once said "Credit card or prepaid card", a name CFPB retired in Aug 2023. Change: prompts will list the allowed labels; scoring is exact match; "outdated label" is the first failure category.
