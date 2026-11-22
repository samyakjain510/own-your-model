# Lesson 5: training a small model, in the cloud

## What "fine-tuning with LoRA" actually does

The base model (Qwen3-4B, 4 billion numbers called weights) already reads English well. It doesn't know the CFPB's 138 product-issue labels or how consumers use them. Fine-tuning shows it thousands of examples ("this complaint → this label") and nudges it toward the right answers.

LoRA leaves the 4 billion weights frozen. It adds a thin layer of new weights (here, about 30 million) next to them and trains only those. That's why it fits on a free GPU, and why the result, an "adapter", is a small file you can share and load on top of the public base model.

## Why it runs on Kaggle and not the laptop

On the laptop, one training step used about 10 GB of the Mac's 16 GB, and the full job would have taken 6 to 10 hours. The Mac hung. Kaggle gives free GPU time (an NVIDIA T4 with 16 GB of its own memory) in the cloud, so the laptop only sends the job and downloads the results.

## Watching for overfitting

The model sees each training example up to twice. Every so often it's scored on 300 complaints it never trains on (the validation set). If that score stops improving while training continues, the model is memorizing instead of learning. We keep the checkpoint from the moment the validation score was best.

## What each run produces

- The adapter file.
- Its answer for every dev complaint, which our own scorer grades the same way it grades Claude.
- Timings: how many complaints per second it answers, and how many tokens go in and come out. The cost model turns those into dollars per 1,000 complaints.

## Smoke test first

The first cloud run is tiny on purpose: 30 training steps, 64 dev complaints. It checks that the code, data and GPU all work together before we spend hours of free GPU quota on the real run.
