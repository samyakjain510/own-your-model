# Competitors: who covers which step of logs-to-decision

Research date: 2026-11-22. Everything below comes from web pages I opened or search results I read. Where I could not confirm something I wrote "unverified".

The pipeline this kit covers, left to right:

1. **Ingest**: load raw logs
2. **Schema**: a standard trace format
3. **Discover**: error discovery, open coding
4. **Eval set**: build a test set from real cases
5. **Judge**: LLM judge, checked against human labels
6. **Data**: training-data curation, dedup, decontamination
7. **Tune**: fine-tuning
8. **Decide**: own-versus-rent cost model with break-even volume

Key: **Yes** = documented feature. **Part** = some of it, or only a vendor claim. **No** = I found nothing. **?** = unverified.

## Coverage table

| Tool | Ingest | Schema | Discover | Eval set | Judge | Data | Tune | Decide |
|---|---|---|---|---|---|---|---|---|
| OpenPipe | Yes (SDK logging) | Part | No | Part | Part | Part (filter and relabel logs) | Yes | No |
| Predibase | ? | No | No | No | No | No | Yes | No |
| Unsloth | No | No | No | No | No | Part (Studio data prep, beta) | Yes | No |
| Axolotl | No | No | No | No | No | No | Yes | No |
| TRL / PEFT | No | No | No | No | No | No | Yes | No |
| Distilabel | No | No | No | No | Part (AI feedback) | Yes (synthetic data) | No | No |
| Argilla | Part (import datasets) | No | Part (manual review) | Part | Part (human labels) | Yes (annotation) | No | No |
| HF AutoTrain | No | No | No | No | No | No | Yes | No |
| Together fine-tuning | No | No | No | No | No | No | Yes | Part (per-job price estimate only) |
| Fireworks fine-tuning | No | No | No | No | No | No | Yes | No |
| OpenAI fine-tuning / distillation | Yes (stored completions) | Part | No | Yes (Evals) | Part | Part (filter stored completions) | Yes, but closing | No |
| LangSmith | Yes | Yes | Part (Insights Agent clusters traces) | Yes | Part (judge prompts; alignment feature unverified) | Part (add traces to datasets) | No | No |
| Braintrust | Yes | Yes | Part (Patterns, preview) | Yes | Part | Part (Loop helps generate dataset rows) | No | No |
| Arize Phoenix | Yes | Yes (OpenTelemetry based) | Part | Yes | Part | Part (datasets for fine-tuning) | No | No |
| Langfuse | Yes | Yes | Part | Yes | Part | Part | No | No |
| cleanlab | Part | No | No | Part | No | Yes (label errors, outliers, duplicates) | No | No |
| TensorZero | Yes | Yes | No | Part | Part | Yes (datasets from stored inferences) | Part (SFT, prompt optimization) | No |
| Kiln | Part | Part | Part | Yes | Yes (judge evals) | Yes (synthetic data) | Yes (via Fireworks, Together, Vertex) | No |
| Tinker (Thinking Machines) | No | No | No | No | No | No | Yes | No |

I did not find any tool in the "Decide" column that builds a break-even model from a team's own volume and quality numbers. Together shows a price estimate before a training job (see its pricing docs), which covers one input to such a model and nothing more.

## Status and license (as of late 2026)

| Tool | License | Status | Source |
|---|---|---|---|
| OpenPipe | Hosted product; its ART library is open source | Acquired by CoreWeave (announced 2025-09-03). CoreWeave said it would keep maintaining ART. Whether the hosted logging product is still sold: unverified | https://techcrunch.com/2025/09/03/coreweave-acquires-agent-training-startup-openpipe/ |
| Predibase | Hosted product; built on open source foundations. LoRAX license: unverified | Acquired by Rubrik (announced 2025-06, closed 2025-07). Rubrik said it would run as its own business unit. No 2026 news found | https://www.businesswire.com/news/home/20250625307989/en/Rubrik-to-Acquire-Predibase-to-Accelerate-Agentic-AI-Adoption |
| Unsloth | Core Apache-2.0. Studio UI is AGPL-3.0 | Active; Studio is in beta | https://github.com/unslothai/unsloth |
| Axolotl | Apache-2.0 (per PyPI and index sites; I did not open the LICENSE file) | Active | https://docs.axolotl.ai/ |
| TRL | Apache-2.0 (per index metadata, last push 2026-04-25) | Active | https://github.com/huggingface/trl |
| PEFT | Unverified. I did not open its repo | Unverified | https://github.com/huggingface/peft |
| Distilabel | Apache-2.0 | Original authors moved on; a community group maintains it | https://github.com/argilla-io/distilabel |
| Argilla | Apache-2.0 | Owned by Hugging Face since June 2024 ($10M per Fortune). Maintenance mode: bug fixes only, no new features | https://github.com/argilla-io/argilla and https://fortune.com/2024/06/14/hugging-face-ceo-10-founders-week |
| HF AutoTrain Advanced | Apache-2.0 (per the 2024 EMNLP paper) | Current maintenance level: unverified | https://aclanthology.org/2024.emnlp-demo.44 |
| Together fine-tuning | Hosted, closed | Active. LoRA is the default mode; billed per token | https://docs.together.ai/docs/fine-tuning/overview |
| Fireworks fine-tuning | Hosted, closed | Active. Managed training is LoRA only; full-parameter goes through a separate Training API | https://docs.fireworks.ai/fine-tuning/supervised-fine-tuning |
| OpenAI fine-tuning / distillation | Hosted, closed | Winding down. New users cannot access it. Eligible existing customers can create jobs until 2027-01-06. gpt-4.1-nano fine-tunes shut down 2026-10-23; gpt-4.1 and gpt-4.1-mini fine-tunes shut down 2027-01-14 | https://developers.openai.com/api/docs/guides/distillation |
| LangSmith | Hosted, closed (LangChain) | Active. Insights Agent is available on Plus and Enterprise cloud plans | https://blog.langchain.com/from-traces-to-insights-understanding-agent-behavior-at-scale |
| Braintrust | Hosted, closed | Active. $80M Series B announced 2026-02-17. Patterns and Debugger in public preview from 2026-09-03 | https://siliconangle.com/2026/02/17/braintrust-breaks-80m-series-b-funding-round-become-observability-layer-ai/ |
| Arize Phoenix | Elastic License 2.0 (source-available; not an OSI open source license). One index site lists a different license, which looks like a metadata error | Active | https://github.com/arize-ai/phoenix |
| Langfuse | MIT for core features | Acquired by ClickHouse (announced 2026-01-16). ClickHouse says it stays open source and Langfuse Cloud keeps running | https://langfuse.com/blog/announcing-acquisition |
| cleanlab | Apache-2.0 on the current GitHub page. Older package listings say AGPL-3.0, so the license changed at some point; I did not find the date | The company (Cleanlab Studio) was bought by Handshake (2026-01-28), reported as a talent-focused deal. The open source library is still public. Studio's future: unverified | https://github.com/cleanlab/cleanlab and https://techcrunch.com/2026/01/28/ai-data-labeler-handshake-buys-cleanlab-an-acquisition-target-of-multiple-others |
| TensorZero | Apache-2.0 | Repository archived by its owner on 2026-06-12 and now read-only | https://github.com/tensorzero/tensorzero |
| Kiln | Core library and REST server MIT; desktop app is source-available and free | Active as far as I can tell (unverified beyond the README) | https://github.com/Kiln-AI/Kiln |
| Tinker | Hosted, closed | Generally available since 2025-12-12 | https://siliconangle.com/2025/12/12/thinking-machines-makes-tinker-ai-fine-tuning-service-generally-available/ |
| Humanloop (for reference) | Hosted, closed | Team joined Anthropic in 2025-08. The platform was sunset on 2025-09-08 | https://techcrunch.com/2025/08/13/anthropic-nabs-humanloop-team-as-competition-for-enterprise-ai-talent-heats-up |

## Things worth knowing

- **Consolidation is heavy.** OpenPipe, Predibase, Langfuse, Cleanlab and Argilla all changed hands between 2024 and 2026, and Humanloop shut down. A kit with plain files in and plain files out does not depend on any one vendor surviving.
- **The closest open source neighbors have gone quiet.** TensorZero (logs to datasets to fine-tuning) was archived in June 2026. Argilla is in maintenance mode, and Distilabel is run by volunteers. Kiln is the most active open project I found that touches evals, data and fine-tuning together, and it is built around a desktop app where you create data inside Kiln, with no step for starting from an existing pile of logs (my reading of its README; unverified).
- **OpenAI's own fine-tuning route is closing.** Its docs also say to build evals first and fine-tune afterward.
- **Vendor claims I could not verify:** Braintrust's Loop generating whole eval suites (the sources only confirm dataset rows and prompt optimization), and whether LangSmith's Align Evals is still offered.
