# Phase 0: Models, trainers, free compute, and price inputs

Research date: 2026-11-22. Every number below has a link. "Accessed" means the page was read on 2026-11-22. A number marked **unverified** has no solid source or comes from a forum post, a blog with no stated method, or my own arithmetic.

Hard rule for this project: spend $0. No API keys, no paid GPUs, no sign-ups that need a card. Nothing was downloaded or bought during this research.

---

## 1. Open models

### Short list

All sizes are from the Hugging Face model cards (accessed 2026-11-22). Gemma is left out on purpose.

| Model | Params | License | Context | Released | MLX-LM | Unsloth |
|---|---|---|---|---|---|---|
| [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) | 4.0B (3.6B without embeddings) | Apache 2.0 | 262,144 | 2025 (card has no exact date) | Yes. `qwen3` folder in [mlx-lm models](https://api.github.com/repos/ml-explore/mlx-lm/contents/mlx_lm/models) | Yes. Unsloth lists "Qwen3-2507-4B" notebooks on its [notebooks page](https://unsloth.ai/docs/get-started/unsloth-notebooks) |
| [Granite-4.1-3B](https://huggingface.co/ibm-granite/granite-4.1-3b) | 3B | Apache 2.0 | 131,072 | 2026-04-29 | `granite` folder exists in mlx-lm; Granite 4.1 itself is **unverified** | Granite 4.0-H has a Unsloth Colab notebook ([notebooks page](https://unsloth.ai/docs/get-started/unsloth-notebooks)); Granite 4.1 is **unverified**. Axolotl lists "Granite 4" ([Axolotl README](https://github.com/axolotl-ai-cloud/axolotl)) |
| [Phi-4-mini-instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct) | 3.8B | MIT | 128K | 2025-02 | Yes. `phi3` folder in mlx-lm | Phi-4 (14B) has Unsloth notebooks; the mini size is **unverified** |
| [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | 4B (5B in file metadata, includes a vision part) | Apache 2.0 | 262,144 (up to about 1M with YaRN) | 2026-02 | Yes. `qwen3_5` folder in mlx-lm | Yes, with caveats listed below |
| [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | 9B | Apache 2.0 | 262,144 | 2026-02 | Yes | bf16 LoRA needs about 22 GB, so it does not fit a free T4 |
| [SmolLM3-3B](https://huggingface.co/HuggingFaceTB/SmolLM3-3B) | 3B | Apache 2.0 | 65,536 (128K with YaRN) | 2025-10 | Yes. `smollm3` folder in mlx-lm | **Unverified** (not on the Unsloth notebooks page) |
| [Ministral-3-3B-Instruct-2512](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512) | 3.4B language model plus 0.4B vision encoder | Apache 2.0 | 256K | about 2025-12 (card gives no date) | Yes. `ministral3` folder in mlx-lm | Unsloth lists "Ministral 3" ([notebooks page](https://unsloth.ai/docs/get-started/unsloth-notebooks)); Axolotl lists Ministral3 |
| [Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) | 3.21B | Llama 3.2 Community License (custom) | 128K | 2024 | Yes. `llama` folder | Yes (Kaggle notebook exists) |

Other facts behind the table:

- Qwen3 original sizes (1.7B, 4B, 8B and others) are Apache 2.0, with 32K native context and up to 131K with YaRN, per the [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/) and [Hugging Face cards](https://huggingface.co/qwen/Qwen3-1.7B). The blog table says 128K for 8B and the cards say 32K native plus YaRN, so read the card for the exact model.
- Qwen3.8 exists, but the only official dense size I found is 27B ([search result summary](https://the-decoder.com/alibabas-qwen-team-releases-qwen-3-8-models-with-open-weights-under-the-apache-2-0-license/)). The 2B and 4B "Qwen3.8" models on Hugging Face come from third parties and sit on the Qwen3.5 design. They are out of scope.
- Granite 4.1 comes in 3B, 8B and 30B dense, all Apache 2.0, released 2026-04-29 ([IBM Research blog](https://research.ibm.com/blog/granite-4-1-ai-foundation-models), [8B card](https://huggingface.co/ibm-granite/granite-4.1-8b)). The 8B has 131,072 context.
- The Llama 3.2 license asks for "Built with Llama" credit, limits very large products (over 700 million monthly users), and puts a naming rule on models trained from its outputs ([card](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)). That makes it a poor fit for an open-source portfolio repo.
- Qwen3.5 uses a hybrid design (Gated DeltaNet plus attention layers). Per Unsloth's [Qwen3.5 fine-tuning guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune): it needs Transformers v5, it compiles custom Triton kernels (slow to start on T4), and Unsloth does **not recommend QLoRA** for any Qwen3.5 model. Its bf16 LoRA memory figures are about 3 GB (0.8B), 5 GB (2B), 10 GB (4B) and 22 GB (9B). Those figures are Unsloth's own.

### Recommendation: three models

1. **Qwen3-4B-Instruct-2507.** Apache 2.0, plain dense design, answers directly with no thinking block (the [card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) says it has no thinking mode, which keeps JSON output short and easy to parse). Works with MLX-LM and has Unsloth notebooks. Best-supported choice for a first run.
2. **Granite-4.1-3B.** Apache 2.0, plain dense transformer, trained for enterprise tasks, from a different company than the first model. That gives the comparison a second family. Risk: I could not confirm Unsloth or MLX-LM support for the 4.1 release by name. Check this on day one with a 20-step smoke run. If it fails on Unsloth, plain TRL+PEFT should work because the card lists standard Transformers support.
3. **Phi-4-mini-instruct.** MIT license, 3.8B, 128K context. It is the oldest of the three (2025-02), but its design is mature in every tool. A third family and the most permissive license. Swap in SmolLM3-3B if Phi-4-mini gives trouble.

Optional fourth run, only if free hours remain: **Qwen3-8B with QLoRA** on a Kaggle T4. Unsloth's [requirements page](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements) lists 6 GB for 8B QLoRA, so it fits. It gives one point at a larger size for the cost model.

Skip Qwen3.5 for the first pass. It is newer and strong, but the Unsloth guidance against QLoRA, the Transformers v5 requirement and the slow kernel build on T4 add risk on free hardware. Revisit it with Qwen3.5-4B in 16-bit LoRA (about 10 GB per Unsloth) once the first three models work.

---

## 2. Trainers

| Tool | Status (accessed 2026-11-22) | Fit for this project |
|---|---|---|
| [Unsloth](https://github.com/unslothai/unsloth) | PyPI version 2026.11.9, released 2026-11-20 ([PyPI](https://pypi.org/project/unsloth/)). Core is Apache 2.0; the Studio UI is AGPL-3.0. Runs on Windows, Linux, WSL and macOS per the README. Requires CUDA compute capability 7.0 or higher ([requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements)). The project claims 2x faster training and 70% less memory ([README](https://github.com/unslothai/unsloth)); that is its own claim with no independent benchmark. | Main trainer on Kaggle and Colab T4. |
| [TRL + PEFT](https://github.com/huggingface/trl/releases) | TRL v1.18.2 published 19 Nov per the releases page (year not shown on the page). v1.18.0 added support for Qwen3.5 hybrids and v1.17.0 needs `transformers>=5.22.0` for one example. | Fallback when Unsloth does not support a model. Slower and uses more memory than Unsloth. No speed number found. |
| [Axolotl](https://github.com/axolotl-ai-cloud/axolotl) | Apache 2.0. Changelog newest entry 2026/10. LoRA and QLoRA supported. Lists Qwen3, Qwen3.5, Qwen3.6, Granite 4 and Ministral3. Hardware listed is NVIDIA and AMD only; the README does not mention Mac. | Works, but config-heavy for a one-person project. Not needed. |
| [MLX-LM](https://github.com/ml-explore/mlx-lm) | PyPI 0.32.2, released 2026-10-16, MIT, Python 3.11 or newer ([PyPI](https://pypi.org/project/mlx-lm/)). Includes `mlx_lm.lora` for LoRA and full fine-tuning. | The Mac path. See below. |

### Can an M4 with 16 GB fine-tune a 1.5 to 4B model with MLX-LM?

Probably yes with a 4-bit base model (QLoRA), short examples and a small batch. No published run on a base M4 16 GB for a 3B or 4B model turned up, so treat this as **unverified until the first smoke test**.

What the sources do say:

- The [MLX-LM LoRA guide](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/LORA.md) says a quantized `--model` triggers QLoRA. Its memory tips: lower `--batch-size` (default 4) to 2 or 1, lower `--num-layers` (default 16) to 8 or 4, use `--grad-checkpoint`, and split long examples. It supports chat-format (`messages`) and prompt/completion data. `mlx_lm.fuse` merges the adapter into the model.
- The guide's own speed figure is about 250 tokens per second for Mistral 7B on an M1 Max with 32 GB at batch size 1 and 4 layers.
- A third-party guide lists about 200 tokens per second for an 8B model on an M2 Pro with 16 GB and says QLoRA on 8B fits in 16 GB while plain LoRA does not ([InsiderLLM](https://insiderllm.com/guides/fine-tuning-mac-lora-mlx/)). The page calls these rough numbers.
- An M4 Pro 48 GB run of Qwen3-0.6B (bf16, 1,024 context, batch 1) showed about 2.2 iterations per second and 2.6 GB peak ([mlx-tune performance page](https://arahim.dev/mlx-tune/performance.html)), which the author calls rough. The same page says that under 16 GB you should stay with 4-bit models of 0.5 to 1B at 1,024 context or less. That advice is for its own tool, mlx-tune, and is more cautious than the MLX-LM guide.
- Inference peak memory for Qwen3-4B 4-bit on an M4 16 GB was 3.1 GB at 4k context ([oMLX benchmark](https://omlx.ai/benchmarks/6bw07j97), 2026-03-16). Training needs more room for activations and optimizer state. How much more is **unverified**.

My arithmetic (unverified): a set of 3,000 complaints at about 400 tokens each is 1.2 million tokens per pass. At 100 to 200 tokens per second that is roughly 1.7 to 3.3 hours per pass. So the Mac suits smoke tests and one small model. Kaggle does the main runs.

Disk: only about 13 GB is free. Download 4-bit MLX versions only (a 4B model at 4-bit is about 2.3 to 2.7 GB; the Q4_K_M file for Qwen3.5-4B is 2.74 GB per [Techplained](https://www.techplained.com/qwen-3-5-apple-silicon), a figure the article checked on 2026-10-24). Delete each base model after its adapter is saved. Nothing was downloaded during this research.

### Can Unsloth run on Kaggle's free GPUs?

- **T4: yes.** Unsloth's [notebooks page](https://unsloth.ai/docs/get-started/unsloth-notebooks) lists Kaggle notebooks (Qwen3 4B GRPO, Qwen3 14B, Phi-4 14B, Llama 3.1 8B, Llama 3.2 1B and 3B, and others) that set `accelerator=nvidiaTeslaT4`.
- **P100: no, by the stated rule.** Unsloth Core needs compute capability 7.0 or higher ([requirements](https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements)). The P100 is a 6.0 card. No source says this about the P100 by name, so that last step is my inference. Pick the T4 in the notebook's accelerator menu.
- T4 has no bf16 support, so training runs in fp16 ([vLLM forum answer](https://discuss.vllm.ai/t/build-issues-when-serving-gpt-oss-20b-on-tesla-t4-gpus-with-vllm/1673)).

---

## 3. Free compute

### Kaggle

| Item | Finding | Source |
|---|---|---|
| Weekly GPU quota | "Up to 30 hours" per week, and it floats (some users saw 37 to 39). Kaggle's docs do not publish a fixed number. Treat 30 hours as an unofficial planning figure. | [Kaggle GPU tips](https://www.kaggle.com/docs/efficient-gpu-usage) (as quoted in search results), [floating quota post](https://www.kaggle.com/product-feedback/173129), [GPUPerHour, 2026-09-21](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |
| Reset | Saturday midnight UTC, per the floating-quota announcement (date of post not shown). Your account page shows the real reset. | [Kaggle post](https://www.kaggle.com/product-feedback/173129) |
| GPU types | T4 and P100 class. The exact menu changes. I could not read Kaggle's notebook docs page directly (it loads with JavaScript), so confirm the menu inside a notebook. | [GPUPerHour, 2026-09-21](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |
| Session length | Sources disagree. A 2026-09 review quotes the current docs as 12 hours for CPU and GPU sessions. An older tips page says 9 hours. Plan for 9 hours and checkpoint every 30 minutes. | [GPUPerHour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits), [Kaggle GPU tips](https://www.kaggle.com/docs/efficient-gpu-usage) |
| Phone verification | Required for GPU and internet access per course guides. No official Kaggle page was readable. Some VoIP numbers reportedly fail. | [Calvin University lab](https://cs.calvin.edu/courses/cs/376/25sp/units/01introduction/lab/), [fast.ai course](https://course.fast.ai/Resources/kaggle.html) |
| Bonus hours | Colab Pro and Pro+ subscribers who link accounts get 15 and 30 extra Kaggle GPU hours per week. Not relevant at $0. | [GPUPerHour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |

### Google Colab (free)

- GPU types vary over time and Google does not name them. Users report a T4.
- Notebooks run at most 12 hours "depending on availability and your usage patterns". Idle timeouts apply. Usage limits are not published.
- Without a paid balance, SSH and remote desktops are prohibited and free runtimes can stop without warning.

Source: [Colab FAQ](https://research.google.com/colaboratory/faq.html) (accessed 2026-11-22), [GPUPerHour, 2026-09-21](https://gpuperhour.com/blog/free-cloud-gpus-and-credits). Unsloth has free Colab notebooks for Qwen3.5 at 0.8B, 2B and 4B ([Unsloth guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune)).

### Other free options

| Option | What you get | Fit | Source |
|---|---|---|---|
| Hugging Face ZeroGPU | 5 minutes of GPU per day on a free account, Gradio Spaces only | Demos. No training. | [GPUPerHour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |
| Lightning AI free plan | One free Studio, restarts every 4 hours; monthly free credit not confirmed | Maybe as a backup. **Unverified** quota. | [GPUPerHour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |
| Modal Starter plan | $30 of compute credit each month, no monthly fee. Whether a card is needed to sign up is **unverified**. At the listed rates that credit covers about 27 hours on an A10 or 50 hours on a T4 (my arithmetic). | Good for a vLLM throughput test later, if sign-up needs no card | [Modal pricing](https://modal.com/pricing) |
| SageMaker Studio Lab | Closed to new customers | No | [GPUPerHour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |
| Paperspace free tier | Free M4000, auto-shutdown at 6 hours; availability untested | Too old and small | [GPUPerHour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |
| AWS, Google Cloud, Azure free trials | Mostly exclude GPUs | No | [GPUPerHour](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) |

---

## 4. Local inference for evaluation

Measured numbers for the exact chip and model are scarce. What exists:

| Setup | Result | Source and date |
|---|---|---|
| Qwen3-4B 4-bit, oMLX v0.2.13, M4 10-core GPU, 16 GB | 30.7 tokens/s generation at 4k context, 37.7 at 1k; prompt processing 346.5 tokens/s at 4k; peak memory 3.1 GB. Batching raises total throughput: 71.3 tokens/s at 2 requests and 88.2 at 4. | [oMLX benchmark](https://omlx.ai/benchmarks/6bw07j97), 2026-03-16 |
| Qwen3.5-9B Q4_K_M, base M4 | Ceiling of about 21 tokens/s from bandwidth arithmetic (120 GB/s divided by a 5.68 GB file). The article states it ran no benchmarks, so this is an estimate. | [Techplained](https://www.techplained.com/qwen-3-5-apple-silicon), file sizes checked 2026-10-24 |
| llama.cpp and Ollama on M4 with 1.5 to 4B models | No trustworthy measured number found. Sites like llmcheck.net publish estimates and say so. | **Unverified** |

Plan: run the evaluation set through MLX-LM on the Mac in batches (the oMLX batching result shows batching helps), and run `mlx_lm.benchmark` and `llama-bench` once on the Mac to record our own tokens-per-second figures for the report. llama.cpp and Ollama need a GGUF file, and the MLX-LM guide says its GGUF export only covers Mistral, Mixtral and Llama-style models in fp16, so GGUF may need to come from llama.cpp's own converter. Treat that as **unverified**.

### vLLM on Kaggle's T4 for throughput measurement

Possible with limits. Findings:

- T4 is compute capability 7.5, supports fp16 only, and recent FlashAttention kernels are not guaranteed there ([vLLM forum](https://discuss.vllm.ai/t/build-issues-when-serving-gpt-oss-20b-on-tesla-t4-gpus-with-vllm/1673)).
- A community package, [kaggle-vllm](https://pypi.org/project/kaggle-vllm/), targets Kaggle's two-T4 setup with CUDA 12.8. It says it is not an official Kaggle or vLLM build. A [Hugging Face repo](https://huggingface.co/waqasm86/vllm-kaggle-models) reports a Qwen2.5-3B run in fp16 on two T4s with `enforce_eager=True`, `max_model_len=2048` and `gpu_memory_utilization=0.70`.
- No published tokens-per-second number for vLLM on a T4 turned up.

Plan: try vLLM with `dtype=half` and `enforce_eager=True` on a Kaggle T4 as a stretch task. A T4 figure is only a proxy for an L4 or A10G, so label it that way. If vLLM fails to run there, use the one published vLLM number below and mark the cost model as based on it.

Published vLLM serving numbers (all vendor blogs, so treat as soft):

- Qwen3-8B on an A10 with vLLM reached 851 tokens/s with a 524 ms median time to first token; Llama 3.1 8B reached 947 tokens/s ([TrueFoundry, July 2026](https://www.truefoundry.com/blog/vllm-benchmark)). Same post notes error rates differ between models, so read it before quoting.
- I found no vLLM figure for a 3B or 4B model on L4, A10G, A100 or H100. Vultr lists Qwen3-4B numbers measured on a B200 ([Vultr](https://docs.vultr.com/models/alibaba-qwen-3/qwen3-4b)), which is not a GPU we price. **Gap**: the cost model needs a tokens-per-second input for a 4B model, so measure it on the T4 or on Modal's free credit, or scale from the A10 8B figure (scaling is my assumption).

---

## 5. Price inputs (nothing is being bought)

### (a) Claude API list prices

Source: [Claude pricing page](https://platform.claude.com/docs/en/about-claude/pricing.md), accessed 2026-11-22. Dollars per million tokens (MTok).

| Model | Input | Output | 5-minute cache write | 1-hour cache write | Cache hit | Batch input | Batch output |
|---|---|---|---|---|---|---|---|
| Haiku 5.5, prompt up to 100k tokens | $0.10 | $0.50 | $0.125 | $0.20 | $0.01 | $0.05 | $0.25 |
| Haiku 5.5, prompt over 100k tokens | $0.50 | $2.50 | $0.625 | $1.00 | $0.05 | $0.25 | $1.25 |
| Sonnet 5.5 | $2 | $10 | $2.50 | $4 | $0.10 | $1 | $5 |
| Opus 5.5 | $4 | $20 | $5 | $8 | $0.20 | $2 | $10 |

Notes from the same page:

- Batch API gives 50% off input and output. Batch and caching discounts stack.
- Cache write multipliers are 1.25x (5 minutes) and 2x (1 hour) of input price. Cache hits on Opus 5.5 and Sonnet 5.5 are 0.05x of input; on most other models 0.1x.
- Claude 4.7 and later use a tokenizer that produces about 30% more tokens for the same text. Count tokens on the model you test.
- US-only inference adds a 1.1x multiplier.
- Haiku 5.5 charges the higher rate when a request's prompt is over 100,000 tokens. Complaint triage prompts will be far under that.

### (b) Hosted open-model per-token prices

All accessed 2026-11-22. Pages show no "last updated" date unless noted. Dollars per million tokens.

| Provider | Model | Input | Output | Source |
|---|---|---|---|---|
| Together | Qwen3.5 9B | $0.17 | $0.25 | [pricing](https://www.together.ai/pricing) |
| Together | Qwen3.8 Flash | $0.15 | $0.47 | [pricing](https://www.together.ai/pricing) |
| Together | gpt-oss-120B | $0.15 | $0.60 | [pricing](https://www.together.ai/pricing) |
| DeepInfra | Qwen3.5-9B | $0.10 | $0.15 | [pricing](https://deepinfra.com/pricing) |
| DeepInfra | Qwen3-14B | $0.12 | $0.24 | [pricing](https://deepinfra.com/pricing) |
| DeepInfra | Llama 3.1 8B Instruct Turbo | $0.02 | $0.04 | [pricing](https://deepinfra.com/pricing) |
| DeepInfra | Phi-4 (14B) | $0.07 | $0.14 | [pricing](https://deepinfra.com/pricing) |
| DeepInfra | Mistral-Small-3.2-24B | $0.075 | $0.20 | [pricing](https://deepinfra.com/pricing) |
| OpenRouter | Qwen3.5-9B, range across providers | $0.08 to $0.17 | $0.12 to $0.25 | [model page](https://openrouter.ai/qwen/qwen3.5-9b) |
| Groq | gpt-oss-20B | $0.075 | $0.30 | [models page](https://console.groq.com/docs/models) |
| Groq | gpt-oss-120B | $0.15 | $0.60 | [models page](https://console.groq.com/docs/models) |
| Groq | Llama 3.1 8B | "Contact Sales" | "Contact Sales" | [models page](https://console.groq.com/docs/models) |
| Fireworks | "From $0.05 per million input tokens"; batch 50% off; cached input 50% off; no 4B to 9B model shown in the page text I could read | n/a | n/a | [pricing](https://fireworks.ai/pricing) |

No hosted price was found for Qwen3-4B-Instruct-2507, Granite 4.1 3B or Phi-4-mini. The nearest proxy for a fine-tuned 4B model served by someone else is the 9B tier at about $0.10 to $0.17 input and $0.15 to $0.25 output. A fine-tuned model also needs a host that accepts custom weights or adapters; that was not checked for these providers, so it is **unverified**.

Fine-tuning as a service, for reference (Together): SFT on Qwen3.5 0.8B to 9B at $0.34 per million training tokens with a $4 minimum; the page also shows a second table with higher rates (for example $0.38 for 9B), and does not say which applies ([Together pricing](https://www.together.ai/pricing)). Fireworks lists dedicated training from $8.00 per GPU-hour ([Fireworks pricing](https://fireworks.ai/pricing)).

### (c) GPU rental per hour

Dollars per GPU-hour, on-demand, accessed 2026-11-22.

| GPU | RunPod (secure cloud) | Lambda | Modal | AWS (us-east-1, Linux, per [Vantage](https://instances.vantage.sh/aws/ec2/g6.xlarge), 2026-11-22) | DeepInfra custom deploy |
|---|---|---|---|---|---|
| L4 24 GB | $0.69 | not listed | $0.80 | $0.805 (g6.xlarge) | n/a |
| A10 / A10G 24 GB | not listed | $1.29 | $1.10 | $1.006 (g5.xlarge, [Vantage](https://instances.vantage.sh/aws/ec2/g5.xlarge)) | n/a |
| A100 40 GB | not listed | $1.99 | $2.10 | $21.958 for 8x in p4d.24xlarge, so about $2.74 each (my division; [Vantage](https://instances.vantage.sh/aws/ec2/p4d.24xlarge)) | n/a |
| A100 80 GB | $2.09 (PCIe), $2.19 (SXM) | $3.19 (8x HGX) | $2.50 | not checked | $1.49 |
| H100 80 GB | $2.89 (PCIe), $4.39 (SXM) | $3.79 (PCIe), $4.59 to $4.89 (SXM) | $3.95 | $55.04 for 8x in p5.48xlarge, so about $6.88 each (my division; [Vantage](https://instances.vantage.sh/aws/ec2/p5.48xlarge)) | $2.90 |

Sources: [RunPod](https://www.runpod.io/pricing), [Lambda](https://lambda.com/pricing) (no effective date on the page), [Modal](https://modal.com/pricing) (per-second rates; hourly figures are my multiplication), [DeepInfra](https://deepinfra.com/pricing) (per-minute billing). RunPod serverless runs higher: $0.75 for 24 GB cards, $2.99 for A100 80 GB, $5.89 for H100. Together lists dedicated H100 at $5.49 and Fireworks at $8.00 per GPU-hour ([Together](https://www.together.ai/pricing), [Fireworks](https://fireworks.ai/pricing)).

Gaps:

- **Google Cloud**: the one Vantage page read showed $0.1468 per hour for g2-standard-4 with one L4 ([Vantage](https://instances.vantage.sh/gcp/g2-standard-4)). That is far below AWS's L4 rate and the page did not confirm region or whether it is spot, so I do not trust it. GCP A100 and H100 rates were not retrieved. **Unverified.** Use AWS as the hyperscaler reference in the cost model.
- The AWS p4d and p5 pages did not label region or operating system in the text I read.
- Third-party sites put Lambda's H100 SXM at $3.99 to $4.29 in mid-to-late 2026 ([Orb summary via search](https://www.withorb.com/pricing-atlas/lambdalabs)). Lambda's own page now shows $4.69 to $4.89, so older figures are stale.

Serving throughput: see the end of section 4. The only published vLLM figures found are for 8B models on an A10.

---

## 6. Using `claude -p` on a Claude subscription

Facts from Anthropic's own pages, accessed 2026-11-22:

- **Scripted runs draw from the plan limits when you sign in with the plan.** Anthropic's support article says that when you are signed in with your Claude plan, the Agent SDK and `claude -p` "still draw from your subscription limits" ([Use the Claude Agent SDK with your Claude plan](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)). A change announced in June 2026 that would have split SDK usage off was paused on June 15, 2026, per the same article.
- **Limits.** Pro and Max have a five-hour session limit and a weekly limit, shared between Claude chat and Claude Code ([Pro and Max plan article](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)). The size of those limits is not stated in tokens or messages on the pages I read, so planning numbers are **unverified**. Expect the limit message ("You've hit your session limit") and build a resume feature. Per the [costs doc](https://code.claude.com/docs/en/costs.md), the limit is shared across models, so switching models inside one family of limits may not help.
- **API credits do not help this project.** Since 2026-10-07 Max, Ultra and Team plans include monthly API credits ($100 for Max, $200 for Ultra, per [the credits article](https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans) as quoted in search results). They apply only when `claude -p` runs with an API key from a linked Console organization, and Pro gets none. With a no-API-key rule they are out of reach.
- **Do not pass `--bare`.** The [headless docs](https://code.claude.com/docs/en/headless) say bare mode never reads OAuth credentials or the keychain, so it needs an API key and ignores the subscription login. The docs also say `--bare` may become the default for `-p` in a future release, so pin the Claude Code version and test the login path before every large batch.
- **Setting `ANTHROPIC_API_KEY` switches to API billing.** The Pro and Max article says that if the variable is set, Claude Code uses it and incurs API charges. Make sure it is unset in the shell that runs the eval.
- **Output JSON includes token usage and cost.** With `--output-format json` the response carries session ID, `usage`, `total_cost_usd` and a per-model `modelUsage` breakdown ([headless docs](https://code.claude.com/docs/en/headless), [cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking.md)). The usage object includes input, output, cache-creation and cache-read token counts. The cost is a client-side estimate at list price, not a bill, and for plan subscribers it does not describe what you pay. Use the token counts as the real measurement and price them with the table in section 5.
- **Structured output.** With `--json-schema`, the result sits in a `structured_output` field. If the run ends without valid structured output (for example the model declined), the field is missing, so the harness must check for it ([headless docs](https://code.claude.com/docs/en/headless)).
- **Where the run starts matters.** Without `--bare`, `claude -p` loads CLAUDE.md, memory, hooks and MCP servers from the working directory and `~/.claude`. Run the eval from an empty temporary folder, keep `--tools ""` and `--no-session-persistence`, and expect extra input tokens from Claude Code's own context. Compare `usage` against a known prompt size once to measure that overhead.
- **Rules on automation.** Anthropic's articles give no specific rule on scripted or automated use beyond the usage limits. Read the [Consumer Terms](https://www.anthropic.com/legal/consumer-terms) before a large unattended batch. I did not read them in this research, so any claim they allow it is **unverified**. Keep runs sequential or low-concurrency, cache results to disk, and resume after a limit message.

For the cost model, treat the subscription as free for this project, record the real token counts from `usage` and price the same tokens at the list prices above to show what the Claude side would cost on the API.

---

## 7. Summary of the plan that fits $0

1. **Day one smoke tests (Mac).** Install `mlx-lm`, run 20 steps of QLoRA on a 4-bit Qwen3-4B-Instruct-2507 with batch size 1 and short sequences. Record peak memory and tokens per second. This fills the gap in section 2.
2. **Main training (Kaggle T4, Unsloth).** Qwen3-4B-Instruct-2507, Granite-4.1-3B and Phi-4-mini-instruct, each as QLoRA, fp16, with checkpoints every 30 minutes. About 30 GPU hours per week is the unofficial quota. Budget two to three hours per model per run, which is my guess based on the 4B model sizes and unverified.
3. **Fallback.** If Unsloth fails on a model, use TRL + PEFT on the same T4. Colab free T4 is the backup for quota or session limits.
4. **Evaluation.** Run each tuned model on the Mac with MLX-LM and record tokens per second with `mlx_lm.benchmark`. Run the same test set through `claude -p` on Haiku 5.5, Sonnet 5.5 and Opus 5.5 and record `usage` per call.
5. **Throughput stretch.** Try vLLM on a Kaggle T4 (fp16, `enforce_eager`) to get a tokens-per-second number for the cost model. Modal's $30 monthly free credit is a second option if sign-up needs no card.
6. **Cost model inputs.** Claude list prices (section 5a), hosted 9B-class prices as the "rent a similar open model" line (5b), GPU hourly rates for L4, A10 or A10G, A100 and H100 (5c), and measured tokens per second from step 4 or 5.

## Open questions to settle first

- Does Granite 4.1 load in Unsloth and in `mlx_lm.lora`? (20-step test each.)
- What is the real peak memory of QLoRA on a 4B model on this Mac?
- Does the Kaggle account pass phone verification, and what weekly hours does its account page show?
- Does `claude -p` on this machine use the subscription login in a clean folder, and how many extra input tokens does it add per call?
- Which provider, if any, hosts a fine-tuned small model for a per-token price? Not checked.
