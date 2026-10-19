# Midterm evidence brief

Exploratory retrieval baseline, not answer-quality or adaptive-system results.

Corpus: 290 documents. Questions: 100; scored: 90.
Code commit: 930cad6ed7de3a1ba2f6385a3009fd92168ad174

## Retrieval metrics

| Group | Scored | Hit@1 | Hit@5 | MRR |
| --- | ---: | ---: | ---: | ---: |
| All (pooled) | 90 | 0.544 | 0.844 | 0.670 |
| Split: dev | 62 | 0.516 | 0.839 | 0.655 |
| Split: test | 15 | 0.467 | 0.800 | 0.589 |
| Split: val | 13 | 0.769 | 0.923 | 0.835 |
| Type: basic | 35 | 0.629 | 0.914 | 0.752 |
| Type: constrained | 15 | 0.867 | 1.000 | 0.933 |
| Type: info_not_found | 0 | N/A | N/A | N/A |
| Type: intra_document_reasoning | 15 | 0.533 | 0.867 | 0.672 |
| Type: semantic | 25 | 0.240 | 0.640 | 0.397 |

## Examples for manual review

Selected deterministically from development questions only. These demonstrate document retrieval, not verified generated answers.

### Rank-one success

Question (qst_0046): In the Medicore procurement email thread about data use and telemetry, what turnaround timeline did Redwood propose for delivering the operational runbook?

Gold document rank: 1. Gold IDs: dsid_3be2b45196414cad9b187551da3ed448.

Top retrieved document: dsid_3be2b45196414cad9b187551da3ed448

### Semantic miss outside top five

Question (qst_0187): When a production model experiment shows a sustained increase in harmful output warnings for two evaluation windows, what automated actions should the platform take regarding traffic shifting and incident/oncall notifications?

Gold document rank: 6. Gold IDs: dsid_a27715e7309c494d812c75cf03bcf916.

Top retrieved document: dsid_2401e6c7889b4c2081c66dae551f434a

## Limits and next steps

- No multi-document gold questions in the current subset; add them before claiming that capability.
- Ten info-not-found questions are unscored for retrieval; refusal behavior has not been implemented or evaluated.
- Split metrics are descriptive. Earlier pooled results have already been inspected; do not present this as a pristine held-out study.
- MRR averages reciprocal rank, not rank. Retrieval success does not prove answer correctness.
- This local baseline has no paid generation calls; zero API spend does not mean zero compute cost.
- Next: grounded generation/refusal, reranking, verified cache and bounded second retrieval, followed by quality/latency/cost comparisons.
