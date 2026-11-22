# Positioning

## The gap

Plenty of tools sit on one side of the middle of this pipeline. Tracing and eval platforms (LangSmith, Braintrust, Phoenix, Langfuse) take logs in and give you dashboards, datasets and judges. Training tools (Unsloth, Axolotl, TRL, Together, Fireworks, Tinker) take a clean dataset in and give you a tuned model. The step between them is thin: a team has a pile of raw production logs and needs an eval set and a training set it can trust.

From what I found, no tool does all of these together:

1. Starts from raw logs in a plain file format.
2. Walks a person through error discovery (open coding, then a failure list).
3. Builds a held-out eval set from those failures.
4. Measures an LLM judge against human labels, with true positive and true negative rates.
5. Checks the historical human labels for errors before calling them ground truth.
6. Produces a training set that has been deduplicated and kept apart from the eval set.
7. Ends with an own-versus-rent cost model with a break-even volume.

The last item is the clearest hole. In the tools I read about, nothing builds a break-even model. Together shows a price estimate for a training job, which is one number a break-even model needs. I found no decision step in any of the others, though I did not read every pricing page.

## Who the user is

An AI product manager or engineering lead at a mid-size company. They run one narrow task at high volume, such as sorting incoming tickets or complaints, and they pay a frontier model per call. They have months of logs and a human-review history. They want to know one thing: would a small open model we run ourselves be good enough, and at what volume does it get cheaper?

## What the kit does

- Takes raw logs for one workflow and turns them into traces.
- Helps find the failure types, then builds the eval set and a judge, and reports how well the judge agrees with people.
- Flags suspect historical labels so they do not silently become the answer key.
- Builds the training set, fine-tunes small open models with LoRA, and compares them with the rented model on the eval set.
- Ends with a cost model and a one-page decision report.
- Uses the CFPB Consumer Complaint Database (complaint routing) as the worked example.

## Where it overlaps with existing tools

- **Tracing and judging:** LangSmith, Braintrust, Phoenix and Langfuse already store traces and run judges. Langfuse is MIT-licensed and Phoenix is source-available (Elastic License 2.0). A team that already uses one should export its traces into this kit and not run a second tracing system.
- **Error discovery:** LangSmith's Insights Agent clusters traces into failure patterns, and Braintrust has a Patterns feature in preview. The kit's error-discovery step covers similar ground. The kit builds that step around a person reading cases and writing notes, as Husain and Shankar describe.
- **Judge alignment:** AlignEval (a web app) and EvalGen (a research tool) both compare judges with human labels. The kit borrows from both.
- **Fine-tuning:** Unsloth, Axolotl and TRL do the training better than a new kit would. The kit calls them and does not replace them.
- **Data curation:** Distilabel, Argilla and cleanlab cover synthetic data, annotation and label-error detection. The kit uses cleanlab's method and may use the library directly. Argilla is in maintenance mode and Distilabel is volunteer-run.
- **Closest overall:** TensorZero (logs to datasets to fine-tuning) was the nearest open source match, but its repository was archived in June 2026. Kiln covers evals, synthetic data and fine-tuning, but from my reading of its README it is a desktop app where you build data inside it (unverified). A reviewer should compare against Kiln before launch.

## Risks to the claim

- I read feature lists from docs and search results, not from hands-on use. Some tools may do more than I credit them with.
- The "unserved" claim is about the combination, and each single piece exists somewhere.
- The YC request names the gap in general terms and says nothing about this specific kit.
- How the CFPB labels were produced and how noisy they are: unverified. I have not yet read the database documentation, so Phase 1 should check it.
