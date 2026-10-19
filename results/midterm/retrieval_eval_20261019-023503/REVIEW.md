# Reproduction and manual example review

Run locally on October 18, 2026 (America/Los_Angeles); output directory uses UTC.

## Reproduction

- All 100 question IDs and gold-document ranks match the saved October 16
  `retrieval_eval_20261016-191756` run exactly.
- 76/90 answerable questions have a gold document in the top five (84.4%).
- 49/90 rank a gold document first (54.4%). MRR is 0.670343.
- Semantic questions: 16/25 Hit@5 (64%), 6/25 Hit@1 (24%).
- Development: 52/62 Hit@5; validation: 12/13; test: 12/15.
- No duplicate question IDs or exact normalized question text were found.
- The corpus byte hash differs from the earlier macOS run because of CRLF
  line endings. Normalizing file line endings to LF reproduces the earlier
  SHA256: `e0e9ad110102f8f124ac51522c2f569e01eca64dd136d3321a8596c5993e9f2d`.
- The index contains 3,358 token-safe passages from 3,098 word-based chunks,
  matching the earlier index count. Paragraph strategy, 120 words, overlap 20.
- Index SHA256: `16177a2b5c096cb8958b8d220a32fbf4d558949727de3028e43bb942d5827294`.
- Downloaded MiniLM snapshot: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
  Installed dependency versions are saved in `environment.txt`.

## Example 1: document retrieval succeeds, but the top passage omits a key detail

Development question `qst_0046` asks for the proposed operational-runbook
turnaround in the Medicore procurement email thread. Gold document
`dsid_3be2b45196414cad9b187551da3ed448` ranks first. Its full text explicitly
proposes a **5-business-day turnaround** for the runbook.

However, the document's best-scoring chunk (`chunk-0006`, character offsets
3024–3587) starts with “for the runbook and 7–10 business days for the redline”.
It omits the preceding five-day detail. This is a document-level success, not
proof of answer-bearing passage retrieval. A generator given only that chunk
could confuse the redline timeline with the runbook timeline. Evaluate passage
coverage and consider adjacent context before claiming answer correctness.

## Example 2: semantic retrieval misses the top-five cutoff

Development question `qst_0187` asks which automated actions follow a sustained
increase in harmful-output warnings over two evaluation windows. Gold document
`dsid_a27715e7309c494d812c75cf03bcf916` ranks sixth. Its AC7 explicitly specifies
shifting up to 75% of traffic to the last-known-good model, opening an incident,
and notifying on-call via PagerDuty and the Console channel.

The top-ranked passage instead introduces a general field guide about service
degradation and notification procedures. It is topically related but does not
state the requested model-quality remediation rule. This example motivates
testing reranking or improved retrieval; it does not prove either will help.

## Timing and claim boundaries

Measured mean retrieval latency was approximately 359 ms, p95 approximately
293 ms. The mean includes the first query's model-loading overhead. These are
single-run local timings for query embedding, exhaustive scoring, and document
ranking, not production latency or full answer-generation latency. Use quality
metrics as the main midterm evidence, not this timing as a cost-saving claim.

The ten info-not-found questions remain unscored for refusal. All answerable
questions have one gold document. Earlier pooled results were inspected, so
split results are descriptive rather than a pristine held-out final evaluation.

**Suggested takeaway:** The baseline retrieves a gold document in the top five
for 84.4% of answerable questions, but semantic queries and answer-bearing
passage coverage remain weaknesses. Adaptive cost savings are not yet measured.
