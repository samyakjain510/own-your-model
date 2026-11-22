# Prior work this kit builds on

Each entry gives the method in a few bullets, then one line on how this kit uses it. Facts come from the linked pages. Where a page was too long for me to read in full, I say so.

## 1. Husain and Shankar: error analysis before metrics

Link: https://hamel.dev/blog/posts/evals-faq/ (the AI Evals FAQ; the page is long and I read roughly the first 100,000 of its 154,000 characters).

- Start by reading real traces. A domain expert writes free-form notes about what went wrong, noting the first failure in each trace. This is open coding.
- Then group the notes into a list of failure types and count how often each one happens. This is axial coding. The FAQ calls it the most important step.
- Keep going until new traces stop turning up new failure types.
- The FAQ recommends binary pass/fail labels over 1-to-5 scores, because adjacent scores are subjective and people label them inconsistently.
- To trust a judge, check it against human labels using two rates: the true positive rate (how many real failures it catches) and the true negative rate (how many good outputs it passes). Split the labeled data into train, dev and test, and look at the test set last.
- Suggested sizes: review at least 100 traces; for judges, at least 50 passing and 50 failing labeled examples, and 100 to 200 labeled examples per failure type.
- Related pieces: the Pragmatic Engineer write-up at https://newsletter.pragmaticengineer.com/p/evals (partly paywalled, so I only saw a search snippet) and Husain's judge guide at https://hamel.dev/blog/posts/llm-judge/ (only seen in search results).

**How the kit uses it:** the error-discovery step samples complaints, writes open codes, groups them into a failure list, and the judge step reports true positive and true negative rates on a held-out test split for one pass/fail judge per failure type.

## 2. "Who Validates the Validators?" (EvalGen)

Link: https://arxiv.org/abs/2404.12272 (Shankar, Zamfirescu-Pereira, Hartmann, Parameswaran, Arawjo; UIST 2024). I read the abstract and search summaries, not the full paper.

- EvalGen is a tool that proposes criteria and several ways to check each one (code or an LLM judge).
- It asks the person to grade a sample of outputs, then keeps the checks that agree best with those grades.
- The authors name "criteria drift": people need criteria to grade outputs, and grading outputs changes what the criteria are.
- Their conclusion is that you cannot fully write down the criteria before a human has looked at outputs. Some criteria only show up after seeing real outputs.
- They recommend tools that make it fast to revise criteria after more grading.

**How the kit uses it:** the judge rubric is versioned, and every rubric change re-scores the same human-labeled set, so a reader can see how the rubric moved as labeling went on.

## 3. Eugene Yan: AlignEval

Link: https://eugeneyan.com/writing/aligneval/

- Upload a CSV of input, output and a binary label, then label samples pass or fail yourself. Yan suggests 50 to 100 labels; the app turns on evaluation at 20.
- Write one single-question judge prompt and compare it with your labels using recall, precision, F1 and Cohen's kappa.
- Tune the prompt on a dev split and score the best version once on a test split. His example showed F1 of 0.571 rising to 0.722 on dev and then 0.727 on test, with 25 examples per split.
- He warns that small samples give unstable numbers (around 20 labels can swing between reruns), and that a big gap between dev and test points to an unrepresentative dev set.
- He says to write criteria after looking at the data.
- The app was in early beta when he wrote about it, and the optimizer is described as beta.

**How the kit uses it:** the judge report includes Cohen's kappa next to the true positive and negative rates, and prints a warning when the dev-versus-test gap is large or the label count is low.

## 4. Teresa Torres: Interview Coach evals

Link: https://www.producttalk.org/interview-coach-evals/

- She logged the transcript, system prompt and the coach's feedback for each run, reviewed them one by one, and wrote notes.
- From the notes she listed the common failures, such as suggesting leading questions or general questions, or asking something the participant had already answered.
- Each failure got its own check: an LLM judge for leading questions, a keyword search for general questions ("the simplest, dumbest eval" in her words), and plain code for another.
- She compared each check with her own labels. Disagreements sometimes showed her labels were inconsistent, and she revised the rubric.
- The first review round covered about 20 traces; her ongoing dev set has 25 transcripts. Failures of one type fell from 4 of 20 to 1 of 25 after prompt changes.

**How the kit uses it:** each discovered failure type gets the cheapest check that works (code rule first, LLM judge only when a rule fails), and judge-versus-human disagreements are saved for review so the rubric can be fixed.

## 5. Confident learning and label noise

Links: https://arxiv.org/abs/1911.00068 (Northcutt, Jiang, Chuang; JAIR 2021) and https://arxiv.org/abs/2103.14749 (Northcutt, Athalye, Mueller; ICLR 2021 workshop).

- Confident learning estimates which labels in a dataset are probably wrong, using a model's predicted probabilities and a per-class estimate of how labels get mixed up.
- It works without assuming a particular data type or model, and it is implemented in the open source cleanlab package.
- The test-set paper found label errors in 10 widely used datasets, at least 3.3% on average. Humans confirmed about 51% of the algorithm's flagged candidates as truly mislabeled.
- The authors report that model rankings on those benchmarks did not change after removing the errors.
- The cleanlab repo describes a Datalab tool that checks a dataset for outliers, duplicates and label errors (https://github.com/cleanlab/cleanlab).

**How the kit uses it:** Historical labels from people can contain mistakes, so the kit treats them as noisy ground truth (how the CFPB labels were produced: unverified). It runs a label-error pass, sends flagged rows to a human check, and keeps flagged rows out of the eval set and training set until they are reviewed.

## 6. YC Request for Startups, Winter 2027: "Own Your Intelligence"

Link: https://www.ycombinator.com/rfs (written by Jon Xu, per the page I fetched).

- The request says most companies building with AI rent their intelligence from frontier labs, and that open-weight models are now strong enough for companies to own and improve their own.
- It says someone has to turn workflows into evals and expertise into training data.

**How the kit uses it:** this is the stated gap the first half of the pipeline (logs to eval set and training data) is built to fill.
