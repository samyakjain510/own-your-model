# Lesson 4: turning logs into training data

## Half the logs are copies

In the six months before our cutoff, 49.7% of complaints were word-for-word copies of another complaint, mostly template letters from credit-repair services. If we trained on raw logs, the model would mostly learn to recognize one letter. So each set of copies becomes one example.

## Copies vote on the label

When the same text was filed several times, the copies didn't always carry the same label. We used the most common label among them, which is majority voting with no human or model involved. It changed 378 labels.

## How messy are the labels?

Two identical complaints picked at random get the same product *and* issue label 90.6% of the time. So even a perfect reader of the text would miss about 1 in 10 on these. Many copies are probably the same person refiling, so unique complaints may be messier still. Either way it's a useful yardstick: when a model scores far below that, the problem is the model.

## Keeping the exam sealed

Before sampling, we threw out anything that looked like a dev or test complaint: exact matches, then near-matches (80%+ of 5-word chunks shared). That removed 6. Then an independent second check ran on the final set and found nothing.

## Learning curve

We built nested sets of 500, 2,000 and 8,000 examples. Training on each and testing on the same frozen exam shows how quality grows with data. That answers a real business question: "how many past examples do we need before owning a model pays off?"

## A short prompt is a cheap prompt

Claude needs the full list of 138 product-issue labels in every prompt (~1,060 input tokens per complaint). The small model learns the labels during training, so its prompt is just the company and the complaint. Fewer tokens per request means a cheaper and faster model to run, and the cost model will count that.
