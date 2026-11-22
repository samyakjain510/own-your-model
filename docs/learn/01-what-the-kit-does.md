# Lesson 1: what the kit takes in and what it gives back

## Who uses it

Someone at a company with one narrow job that happens thousands of times a month. Today a person or a rented model like Claude does that job. Think of an engineer or a technical PM who has been asked "could we do this cheaper or in-house?" and has no good way to answer.

## What they bring

The main input is data. They bring their **logs**: a file of past examples, each showing what came in and what decision was made. For example, every support ticket from last year and the team it was sent to. A few thousand rows is the floor; more is better.

Next to that comes a short **config file**, about ten lines, that says:

- which column is the input (the ticket text),
- which columns are the decision (team, priority),
- how many of these they expect per month,
- which models to compare, and what their hardware and engineers cost.

## What the kit does with it

This part takes hours, because it does real work:

1. Cleans the logs and strips personal info.
2. Finds where the past decisions look wrong or inconsistent.
3. Builds a test with known right answers, sealed off from the training data.
4. Runs a rented model (Claude) on the test.
5. Trains small open models on the past examples and runs them on the same test.
6. Measures speed and cost, then puts the measured numbers into the cost model.

## What they get back

- A **scorecard**: how often each model got the decision right on their own data, with a range of likely values.
- **Trained adapters** they can run on their own machines.
- A **one-page decision**: cost per 1,000 tasks for each option, the monthly volume where owning starts to win, and a plain list of cases where the small model still fails.

Calculators that guess quality from public benchmarks already exist. The point of this kit is that the quality numbers come from the user's own data.

## What version 1 covers

Version 1 only handles jobs where the answer is a **pick from a fixed list**: routing, tagging, sorting into categories, possibly several fields at once. For these, plain code can grade an answer ("did it pick the right team?"), so we don't need a human to check the grader.

Jobs where the answer is free text, such as writing a reply or a summary, are out for version 1. Grading those needs an AI judge, and an AI judge needs a human to check it, which we've decided not to do here. Version 2 could add them.

## How the case study fits

We're the kit's first user. We bring CFPB complaint logs, the decision is "which product and issue is this complaint about?", and we run the whole thing. The case study shows the kit working on real data. The kit is what someone else would take and run on theirs.
