# Lesson 0: the big picture

Written for Samyak. One of these gets added at each phase.

## The business problem

Companies use models like Claude by renting them: every request costs a little money, and the company has no control over the model. For big, open-ended work that's a good deal. Lots of company work is narrow and repetitive, though: reading a support ticket and deciding which team gets it, pulling fields out of a form, tagging an email. For jobs like that, a much smaller model might do just as well if it has seen thousands of the company's own past examples. A small model can run on the company's own machines, costs less per request at high volume, keeps the data in-house, and never changes unless the company changes it.

Most companies never find out if this works for them, because three things are hard:

1. **They have no test.** Nobody has written down what "doing the job well" means in a way a computer can check. Without that, you can't compare two models.
2. **Their examples are messy.** The history of past work sits in logs full of personal info, half-finished records, and mistakes people made.
3. **The cost math is tricky.** Renting a GPU costs money even when it sits idle, and engineers' time costs money too. The question "when is owning cheaper?" depends on volume, and most teams never work it out.

## What we're building

A kit: a set of scripts anyone can download and run. It takes one real workflow from its raw logs all the way to a yes/no answer on "should we own a model for this?". It also produces a public case study that runs the kit on real data.

```
raw logs → traces → find the errors → test set + judge → training set → train small models → cost model → decision
          (the new part: turning logs into a test and training data)   (the proof that it works)
```

## Words you'll see a lot

- **Trace:** one unit of work pulled from the logs: what came in, and what decision came out. For us, one complaint plus the product and issue it was filed under.
- **Eval set (test set):** a frozen set of examples with known right answers. Every model takes the same test, so scores can be compared fairly.
- **Judge:** something that grades a model's answer. Sometimes it's plain code ("does the product match?"). Sometimes it's another AI model, used when the answer needs judgment. You have to check a judge before you trust it.
- **Fine-tuning / LoRA:** taking an existing open model and training it a little more on your own examples. LoRA is a cheap way to do this. Instead of changing all of the model's billions of numbers, you train a small add-on (an "adapter", often a few megabytes) that sits on top of it.
- **Break-even volume:** the number of requests per month at which owning starts costing less than renting.

## Why CFPB complaints

The US Consumer Financial Protection Bureau publishes millions of real complaints about banks, credit cards, mortgages and debt collectors. It's public domain, so we can share everything we build from it. Each complaint was filed under a product and an issue that the consumer picked, which makes it a real routing log with real human decisions in it. Some of those decisions are wrong, which gives us real errors to find.

## Why no money and no hand-labeling changes the design

Usually a person hand-grades a few hundred examples to create the answer key. We aren't doing that. We use the human decisions already in the logs, and we test our AI judge by planting mistakes we know about and checking whether it catches them. That's also closer to what a real team would do, since most teams won't hand-label either. (Details in `docs/PLAN.md`.)
