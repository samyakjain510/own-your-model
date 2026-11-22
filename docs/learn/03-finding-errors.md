# Lesson 3: building the test and finding the first errors

## The past doesn't look like the future

We gathered every complaint with text from Sept 2023 to Aug 2026: 2.32 million. Credit reporting is 74% of the older complaints but only 4% of the newest ones. Debt collection went the other way, from 9% to 31%. A model trained on raw history would mostly learn about credit reports, then meet a mix where those barely appear. That's why we split by date: train on the past, test on the future, as in real life.

## Copies everywhere

When we drew the test set from the newest months, about 1 in 8 complaints we drew was a word-for-word copy of one filed earlier, mostly template letters. If those stayed in, a model could "pass" just by remembering them. The kit removes them and records how many.

## Dev set and test set

A **test set** is like a final exam: you only get to sit it once. A **dev set** is practice questions: you can look at mistakes and change your approach as often as you like.

I made a mistake here. I ran the first trial on the test set and read its errors. Once you've used the exam to change your approach, it can't fairly grade that approach anymore. So that set became the dev set, and I froze a fresh 800-complaint test set. Nobody looks at the new one until the final run, and its fingerprint (a SHA-256 hash) is saved so we'd notice if it changed.

## Reading the mistakes

Haiku got the product right on 79% of 300 dev complaints. I read every miss from the first 100 and sorted them into groups (`docs/phase2/failure-taxonomy.md`). Most weren't Claude being dumb. Many complaints really fit two products, like a debt that shows up on a credit report. The consumer files under the company they're angry at; Claude went by the topic.

The fix was something a real routing team would write down: show the company name and say "route by the kind of account the person has with that company". Product accuracy went from 79.0% to 82.7%.

## Is +3.7 points real?

We scored both prompts on the same 300 complaints and asked: if we re-drew 300 similar complaints many times, how much would the gap move? The answer was a range of +0.0 to +7.3 points. So it's probably a real gain, but a small one. Bigger test sets give tighter ranges, and that's why the final test set has 800 items.

## The big open question

Claude gets product *and* issue right only ~46% of the time. Either it's bad at issues, or consumers pick issues inconsistently. If it's the second, a small model trained on thousands of consumer picks may "beat" Claude by learning their habits, which counts as a real win for matching the log. That's what the next round of error discovery checks.
