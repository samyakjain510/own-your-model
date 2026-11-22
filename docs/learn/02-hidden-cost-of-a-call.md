# Lesson 2: the hidden cost of one call

## What happened

Our first test sent Claude one sentence: a complaint about a late fee. The answer was one short line. The usage report said the prompt was **281,839 tokens**. At API prices that one call would have cost about $0.28 (CLI's estimate, run on 2026-11-22).

The extra tokens came from setup we never asked for. The Claude Code command line loads every connected app (email, calendar, chat, task lists) as tool definitions, and those ride along with every request. Adding one flag, `--strict-mcp-config`, told it to load none of them. The same call then used **902** prompt tokens in a bare test and **2,102** through our runner, which also sends a JSON format rule.

## Why it matters

The cost model multiplies tokens by price. If we had measured with the bloated setup, "renting" would have looked hundreds of times more expensive than it really is, and the small model would have "won" for a bad reason. Real companies hit the same trap: prompts grow as people add rules, examples and tools, and nobody checks the token count.

So the kit records the real prompt size of every call and reports it next to the cost.

## A second thing we saw

We asked the same question twice. The first time Haiku said the product was "Credit card or prepaid card". The second time it said "Credit card". The first is the CFPB's **old** category name, retired in August 2023. Claude knows both naming systems, and without a list of allowed answers it can pick either one.

That's error discovery at work. A model can be "right" in plain English and still be wrong for the workflow, because the workflow needs one exact label from one exact list. The fix is to put the allowed labels in the prompt and score only exact matches. Our first failure category has a name now: **outdated label**.
