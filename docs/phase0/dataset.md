# Phase 0: dataset notes (CFPB Consumer Complaint Database)

Research date: 2026-11-22. Every number below comes from a linked source or from the sample files in `data/sample/`.

## Headline finding: narratives are gone from the live database

On August 14, 2026 the CFPB said it would stop publishing consumer complaint narratives ([CFPB press release](https://www.consumerfinance.gov/about-us/newsroom/the-cfpb-to-cease-discretionary-publication-of-complaint-narratives-and-visualizations/)). The API release notes list this as release 24, September 2026: narratives were removed from the database ([release notes](https://cfpb.github.io/api/ccdb/release-notes.html)).

I checked the live API on 2026-11-22. A call with `has_narrative=true` returns records with no narrative field, and the filter has no visible effect (the total stays at 19,371,701 either way). The CSV header of the full download (`complaints.csv.zip`) also has no narrative column.

The CFPB moved the old narratives into its FOIA Reading Room as 21 monthly or multi-month ZIP files, covering complaints received December 1, 2011 through August 14, 2026 ([Narratives Archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/)). That archive is now the source for narrative text. The sample in this repo comes from it (details in "The sample").

## License and redistribution verdict

Verdict: free to use and to redistribute, including a cleaned subset on Hugging Face and models trained on it. I am not a lawyer, and the sources are less direct than I would like.

What supports this:

- Every API response carries `"_meta": {"license": "CC0"}`. I saw this in live responses on 2026-11-22. CC0 gives up copyright claims to the fullest extent the law allows.
- The CFPB's own Hugging Face dataset card is tagged `cc0-1.0` ([CFPB/consumer-finance-complaints](https://huggingface.co/datasets/CFPB/consumer-finance-complaints)).
- CFPB source code is "in the public domain by default within the United States, as a work of the U.S. Government" ([release notes](https://cfpb.github.io/api/ccdb/release-notes.html)).
- For the narratives, the CFPB says it "considers previously published narratives to be in the public domain for Freedom of Information Act (FOIA) purposes" ([press release](https://www.consumerfinance.gov/about-us/newsroom/the-cfpb-to-cease-discretionary-publication-of-complaint-narratives-and-visualizations/)).

Gaps to keep in mind:

- The FOIA public-domain sentence is about FOIA. The Narratives Archive page states no license, no terms of use and no scrubbing description. The CC0 tag appears in the API, which no longer serves narratives.
- I found no attribution requirement. Citing the CFPB is still good practice, and the project should say the data is a CFPB work and link the source files.
- The database says it is "not a statistical sample of consumers' experiences" and that complaints are not representative ([database page](https://www.consumerfinance.gov/data-research/consumer-complaints/)). Say this in any write-up.
- Narratives are unverified, one-sided statements by consumers. The CFPB itself gives that as its reason for ending publication.

Practical rule for the repo: publish a small cleaned subset with a README that names the CFPB as the source, links the archive file, states the CC0 tag, and lists the redactions applied. Adapters trained on it carry no extra data license obligation that I could find, but state the training data in the model card.

## Where to get the data now

| Source | Has narratives? | Notes |
|---|---|---|
| Search API `https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/` | No (since the 2026 change) | Still returns product, sub-product, issue, sub-issue and the other metadata. |
| Full CSV ZIP `https://files.consumerfinance.gov/ccdb/complaints.csv.zip` | No | 370,737,795 bytes on 2026-11-22. Too large for our disk rule, so I only read its header. |
| FOIA Narratives Archive, 21 ZIPs under `https://files.consumerfinance.gov/f/documents/` | Yes | One CSV per ZIP. July 2026 ZIP is 16,958,404 bytes. Some are over 50 MB (for example Nov-Dec 2025 is 63,867,562 bytes). |
| [CFPB/consumer-finance-complaints](https://huggingface.co/datasets/CFPB/consumer-finance-complaints) on Hugging Face | Old snapshot, last modified 2024-07-16 | Hosted as a loading script only. Not checked further. |

Servers note: `files.consumerfinance.gov` returned HTTP 403 now and then (including for one HEAD request with a custom User-Agent) and 200 on retry. The fetch script retries.

## API details that worked

Endpoint: `https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/` (GET, no key needed).

Parameters I used successfully: `size`, `no_aggs=true`, `sort=created_date_desc`, `date_received_min`, `date_received_max` (format `YYYY-MM-DD`), and `size=0` to get only the aggregation counts per product. The CFPB's API page is [cfpb.github.io/api/ccdb/api.html](https://cfpb.github.io/api/ccdb/api.html); I could not read the parameter list from it, so `frm`, `product` and `format` are untested here. `field=complaint_what_happened` is rejected with `"complaint_what_happened" is not a valid choice`.

Example probe used for this research:

```
https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/?size=1&no_aggs=true&has_narrative=true&sort=created_date_desc
```

Response shape: Elasticsearch-style. Records are in `hits.hits[]._source`, the total is in `hits.total.value`, aggregations are under `aggregations`, and `_meta` holds `license`, `last_updated`, `total_record_count` and flags such as `is_data_stale`.

## Fields

API JSON (`_source`), as returned on 2026-11-22: `complaint_id`, `date_received`, `date_sent_to_company`, `product`, `sub_product`, `issue`, `sub_issue`, `company`, `company_public_response`, `company_response`, `timely`, `submitted_via`, `state`, `zip_code`, `tags`. There is no narrative field any more.

CSV column names: the archive CSV has `Date received`, `Product`, `Sub-product`, `Issue`, `Sub-issue`, `Consumer complaint narrative`, `Company public response`, `Company`, `State`, `ZIP code`, `Tags`, `Submitted via`, `Date sent to company`, `Company response to consumer`, `Timely response?`, `Complaint ID`. The live full CSV has the same columns without the narrative. Field meanings are in the [field reference](https://cfpb.github.io/api/ccdb/fields.html).

Older exports also had `Consumer disputed?` and `Consumer consent provided?`. Release 22 (June 2026) dropped them ([release notes](https://cfpb.github.io/api/ccdb/release-notes.html)).

## Taxonomy history (label drift)

The CFPB keeps each complaint's original choices. The database "preserves the specific products and issues the consumer selected" at filing time ([past updates](https://www.consumerfinance.gov/data-research/consumer-complaints/)). So old and new label names sit side by side.

| Date | Change | Source |
|---|---|---|
| Apr 24, 2017 | 11 forms merged into 1; products cut from 12 to 9; sub-products of "Consumer loan" and "Other financial service" moved into other products; issues and sub-issues merged and reworded | [2017 summary](https://files.consumerfinance.gov/f/documents/201704_cfpb_Summary_of_Product_and_Sub-product_Changes.pdf) |
| Aug 24, 2023 | "Credit card or prepaid card" split into "Credit card" and "Prepaid card"; "Debt or credit management" added (credit repair and debt settlement moved under it); credit reporting product renamed; payday product widened to include advance loans; new mortgage sub-products and sub-issues | [2023 options](https://files.consumerfinance.gov/f/documents/cfpb_consumer_complaint_form_product_issue_options_August_2023_FINAL.pdf) |
| Oct 29, 2026 | "Debanking" added as an issue under "Checking or savings account" and "Credit card" | [2026 options](https://files.consumerfinance.gov/f/documents/cfpb_consumer-complaint-form-product-issue-options_2026.pdf) |

Evidence from the live API (counts by `product`, queried 2026-11-22, all complaints, with and without narratives):

- Jan 1 to Apr 23, 2017 (72,283 complaints): old names such as "Credit reporting", "Bank account or service", "Consumer Loan", "Money transfers", "Prepaid card".
- Apr 24 to Dec 31, 2017 (170,462): 9 products, for example "Credit reporting, credit repair services, or other personal consumer reports" (73,369) and "Credit card or prepaid card" (15,401).
- Jan 1 to Aug 23, 2023 (795,104): the 2017 names, plus 1 each of "Credit card" and "Prepaid card".
- Aug 24 to Dec 31, 2023 (496,939): "Credit reporting or other personal consumer reports" (402,054), "Credit card" (21,871), "Prepaid card" (2,261), "Debt or credit management" (484). Some leftovers with old names also appear in this window: 3,945 under the old credit reporting name and 187 under "Credit card or prepaid card". I did not check why; late-processed complaints are one possibility.

Other release-note dates that touch labels: December 2013 (student loan issues revised, sub-issues added), and release 12, September 2016 (federal student loan servicing and virtual currency added) ([release notes](https://cfpb.github.io/api/ccdb/release-notes.html)).

Consequence for the project: restrict training and testing to one form era, the Aug 24, 2023 to Oct 28, 2026 window. The July 2026 sample sits inside it. Narratives for that era exist in the archive up to August 14, 2026.

## Narrative counts

- Whole database: about 3.8 million complaints with narratives, as reported by a law-firm article written when narratives were still published ([Holland & Hart](https://www.hlc.com/en/publications/consumer-complaint-narratives-controversial-from-the-start-no-longer-included-in-cfpb-database)). This is a secondary source and I did not confirm it against the CFPB files. The API can no longer count narratives.
- Total complaints in the live database: 19,371,701 (API, 2026-11-22).
- July 2026 archive file: 672,036 complaints, of which 10,002 have a narrative (about 1.5 percent). I counted these by streaming the CSV.
- Narratives exist only when the consumer agreed to publish them. They start with complaints received March 19, 2015 ([release notes](https://cfpb.github.io/api/ccdb/release-notes.html)).

Product mix of the 10,002 July 2026 narratives (my count from the archive CSV):

| Product | Narratives |
|---|---|
| Debt collection | 2,727 |
| Checking or savings account | 2,025 |
| Credit card | 1,822 |
| Money transfer, virtual currency, or money service | 781 |
| Mortgage | 728 |
| Vehicle loan or lease | 509 |
| Credit reporting or other personal consumer reports | 463 |
| Payday loan, title loan, personal loan, or advance loan | 410 |
| Student loan | 310 |
| Prepaid card | 134 |
| Debt or credit management | 93 |

## How narratives are scrubbed

- The CFPB's 2015 policy statement ([80 FR 15572](https://files.consumerfinance.gov/f/201503_cfpb_disclosure-of-consumer-complaint-narrative-data.pdf)) says publication needs the consumer's opt-in consent and a scrubbing standard modeled on the HIPAA Safe Harbor method. It also removes demographic details (gender, age, race, ethnicity), financial identifiers such as card numbers, and references to third parties other than the company. The method has an automated step and a human quality check. The Bureau describes its steps as meant to "minimize (but not eliminate)" re-identification risk.
- What I see in the data: removed text is replaced with `XXXX`, and dates and amounts show up as `XX/XX/year>` or `{$123.45}`-style tags. In my 300 sample, 235 narratives contain `XXXX` (4,398 `XXXX` tokens in total), 82 contain a masked date, and 133 contain a `{$...}` amount tag.
- Known gaps: the CFPB says scrubbing reduces risk without removing it. Free text can still carry names of companies, lawyers, family members, job titles, places or rare events. In my sample, a regex check for emails, phone numbers, Social Security number patterns, links and 9-plus digit numbers found none. That check is narrow and does not catch names or addresses.
- ZIP codes: the field may be 5 digits, 3 digits or blank, depending on population, per the [data-use page](https://www.consumerfinance.gov/complaint/data-use/).

## The sample

Files:

- `data/sample/cfpb_sample.jsonl`: 300 complaints, one JSON object per line.
- `data/sample/cfpb_sample.meta.json`: source URL, date fetched, counts, SHA-256 (`07eaea2a8ff2a30c7d064c2926bf4982c9bb48dbd90a70475dbfe2a620fc1c26`).
- `scripts/fetch_cfpb_sample.py`: standard-library script. Run `python3 scripts/fetch_cfpb_sample.py --cafile /etc/ssl/cert.pem` (the `--cafile` flag is only needed for a macOS python.org build with no certificates).

The task asked for the search API. The API no longer returns narratives, so the script reads one archive ZIP instead (July 2026, 16,958,404 bytes, 50 MB cap built in). Rows keep the CSV's own column names and values, unmodified. The script keeps rows with a narrative received on or after `--date-min` (default 2026-07-01), then draws an equal share per product with `--seed 42`, so every product appears. Because of that, the counts below are balanced by design. They do not show the real class mix; use the table above for that.

Counts per product in the 300-complaint sample:

| Product | Count |
|---|---|
| Credit reporting or other personal consumer reports | 28 |
| Credit card | 28 |
| Checking or savings account | 28 |
| Mortgage | 27 |
| Student loan | 27 |
| Payday loan, title loan, personal loan, or advance loan | 27 |
| Money transfer, virtual currency, or money service | 27 |
| Prepaid card | 27 |
| Debt collection | 27 |
| Debt or credit management | 27 |
| Vehicle loan or lease | 27 |

Other facts from the sample: narrative length is 9 to 1,458 words (median 179.5, mean about 237); 65 distinct product and issue pairs; 38 distinct product and sub-product pairs; every complaint came in through the web; 88 have no sub-issue (Debt or credit management 27, Money transfer 27, Payday and similar loans 27, Prepaid card 6, Credit reporting 1), so sub-issue works as a label for only some products.

## Three example narratives

Excerpts are short; the labels are the consumer's own picks.

1. Complaint 23887163. Product: Student loan. Issue: Dealing with your lender or servicer. Sub-issue: Problem with customer service. Text: "MOHELA failed to establish reliable contact with me upon initiating the new repayment cycle, sending XXXX physical notifications, which directly resulted in a severe, non-willful credit delinquency."
2. Complaint 23749370. Product: Student loan. Issue: Incorrect information on your report. Sub-issue: Account status incorrect. Text: "Department of Education/Nelnet accounts reporting XXXX days past due XX/XX/year>. I was on military orders during this period XXXX company will not remove XXXX delinquency for this period on Experian, XXXX TransUnion." The story is about a credit report, yet the product is Student loan. A model might call this credit reporting and be marked wrong.
3. Complaint 23804672. Product: Debt or credit management. Sub-product: Debt settlement. Issue: Problem with customer service. Text: "Comenity Bank, which third site for how to make payments and I was unable to login to make payment and they did not provide it." The text describes a payment login problem at a card company, which does not obviously match debt settlement.

## Risks

- Label noise. Consumers pick the product and issue themselves. Examples 2 and 3 show product and text that do not line up. This is what the error-discovery story can use, but it also caps the accuracy anyone can claim. Any "error" a model flags needs a human look before it is called a mistake.
- Taxonomy drift. Three form eras exist (Apr 2017, Aug 2023, Oct 2026) and old names stay in the data. Mixing eras creates fake classes such as "Credit reporting" next to "Credit reporting or other personal consumer reports". Train and test inside one era.
- Class imbalance. In July 2026 narratives, Debt collection has 2,727 and Debt or credit management has 93. Over the full history the credit reporting product dominates (for example 402,054 of 496,939 complaints in Aug to Dec 2023). Use stratified splits and report per-class scores.
- Narratives only exist for about 1.5 percent of July 2026 complaints, and only for consumers who opted in. Opt-in consumers may write differently from those who did not.
- Duplicate and template complaints. Credit-repair companies and letter generators produce repeated text. In my sample, 39 narratives cite the FCRA or section 1681 and 14 cite the FDCPA or section 1692. A quick check with 6-word overlaps found 2 near-duplicate pairs (4 narratives) in 300. Deduplicate by text before splitting, or the same letter will land in both train and test.
- Residual personal information. The scrubbing is partial by the CFPB's own description. Names of companies, people and places can remain. Run an extra pass for emails, phone numbers, addresses and names before publishing any subset, and keep the `XXXX` markers visible so users know text was removed.
- Redaction artifacts. `XXXX`, `XX/XX/year>` and `{$...}` are not natural text. A model can learn them as shortcuts. Decide up front whether to keep, normalize or mask them, and say which.
- Source stability. The live API lost its narratives in 2026. The archive page states no license and could change. Keep a copy of the exact ZIP name, size and SHA-256 you used.
- The CFPB called narratives unverified and one-sided, and the database is not a representative sample. Do not draw conclusions about how common a problem is from this data.

## ABCD (Action-Based Conversations Dataset)

ABCD, from ASAPP (Chen et al., NAACL 2021), has more than 10,000 human-to-human customer-service dialogues with 55 user intents, set at a fictitious online retail company called "AcmeBrands", with sample actions such as searching for jeans, shirts, boots and jackets ([paper](https://arxiv.org/abs/2104.00783), [full text](https://ar5iv.labs.arxiv.org/html/2104.00783)). The GitHub repository states the MIT license ([asappresearch/abcd](https://github.com/asappresearch/abcd)). I did not verify the license of the data files separately from the repository, nor whether a separate data license file exists. The setting is online clothing and accessories retail, so it does not match the complaint-routing story, and I would not use it for this case study.
