# Project plan

## Objective and scope

Based on the repository's Team 13 proposal: evaluate whether cache reuse and
adaptive retrieval reduce mean latency and cost without sacrificing answer
quality. Compare against a fixed single-pass retrieval-and-generation baseline.
Use keyword retrieval, relevance reranking, at most one additional retrieval
round, and explicit refusal when evidence is still insufficient.

The proposal is the requirements source; the sequence, contracts, and evaluation
clarifications below are implementation recommendations. Weeks are relative to
the team's start date. The skeleton makes no model or database commitment.

## Ten-week schedule

| Week | Work | Completion check |
| --- | --- | --- |
| 1 | Confirm dataset access/terms, assign owners, agree schemas and experiment budget | All teammates can run the demo and tests; a small dataset sample is understood |
| 2 | Normalize documents, preserve source IDs, chunk text, prepare question labels | Reproducible corpus manifest and grouped 70/15/15 split; target 300+ questions |
| 3 | Implement keyword retrieval, reranking, and fixed single-pass generation | Baseline returns cited answers or refusal; retrieval is evaluated separately |
| 4 | Integrate storage and initial evaluation | Milestone 1: indexed corpus, basic search/reranker, initial quality/latency/cost results |
| 5 | Add verified-response cache with context and corpus-version keys | Repeated questions reuse verified answers; changed contexts do not collide |
| 6 | Add evidence checks and bounded query rewriting | Trace shows no more than two retrieval rounds; unsupported questions refuse |
| 7 | Tune routing on development data; select settings on validation data | Frozen thresholds/configuration and passing pipeline integration tests |
| 8 | Run controlled baseline/adaptive comparisons and ablations | Saved per-question results with model, configuration, usage, timing, and commit IDs |
| 9 | Audit correctness, citations, refusals, cache mistakes, and failure cases | Reviewed examples and quality/cost/latency tables by question category |
| 10 | Final held-out evaluation, report, and demo | Milestone 2: reproducible comparison explaining where adaptation wins or loses |

Week 4 storage work should evaluate the proposal's vector/NoSQL options and
record the chosen tools and rationale. The in-memory demo is only scaffolding.
Fine-tuning a reranker and CARC usage are optional extensions after the baseline
and evaluation work; they must not block the core comparison.

## Six suggested workstreams

| Owner slot | Responsibility | First deliverable |
| --- | --- | --- |
| A — Data | Dataset access, parsing, chunking, provenance, split manifests | Sample loader and document/question schemas |
| B — Search | Keyword retrieval, reranking, storage adapters | Baseline retriever implementing the shared interface |
| C — Decisions | Verified cache, evidence checks, routing, query rewriting | Decision rules and route/refusal test cases |
| D — Evaluation | Retrieval metrics, answer rubric, labels, experiment runner | Per-question evaluation record and baseline report |
| E — Integration | Pipeline orchestration, generator adapter, CLI, CI | End-to-end fixed baseline with citations and usage tracking |
| F — Analysis | Experiment design, ablations, error analysis, final report | Comparison template and review rubric |

Agree shared interface changes in a pull request before dependent work begins.
Owners review one another's changes, and integrate a runnable increment weekly.

## Evaluation protocol

- Prepare approximately 300 or more questions covering simple lookups,
  multi-document reasoning, repeats, and unanswerable cases. Record category,
  reference answers, and supporting source IDs.
- Split 70% development, 15% validation, 15% held-out test with a fixed seed and
  saved IDs. Group duplicate/paraphrased questions to prevent leakage. Freeze
  test labels from tuning; do not seed the answer cache with held-out answers.
- Compare fixed single-pass RAG, cache plus fixed RAG, adaptive retrieval without
  cache, and the full system. Hold corpus, generator, and base retrieval settings
  constant. Report cold-cache and controlled warm-cache runs separately.
- Measure retrieval precision@k (relevant retrieved passages divided by k),
  optionally recall@k, answer correctness against references, and faithfulness
  of claims to cited evidence. The proposal conflates these: retrieval precision
  is not an answer-correctness metric, and relevant retrieval alone does not
  establish faithfulness.
- Report answer coverage, refusal rate, correct refusals on unanswerable cases,
  and incorrect answers among answered cases so refusal cannot hide poor quality.
- Record mean and p95 end-to-end latency, input/output tokens, provider/model,
  dated pricing assumptions, and total cost divided by correctly answered
  questions. Mark cost per correct answer undefined when none are correct.
  Include router, reranker, cache, and retry overhead, not just generation.
- Define an acceptable quality-loss tolerance and cost/latency targets before
  the final run; report uncertainty and category-level results. Retain the
  strongest fixed approach if adaptive routing does not improve the tradeoff.

## Implementation sequence and risks

1. Stabilize document/evidence/result interfaces and the data loader.
2. Build a reproducible fixed baseline before adding adaptive behavior.
3. Cache only verified responses, keyed by question, authorized context, and
   corpus version; define invalidation before experimenting with fuzzy matches.
4. Calibrate evidence sufficiency on development/validation examples, including
   misleading lexical matches. Cap retrieval at two rounds and define refusal.
5. Add timing and usage tracking to every component, then evaluate ablations.

Choose model/provider, storage, reranker, dataset subset, and spending cap as a
team in weeks 1–2. Save decisions and experiment configurations in the repository.
Do not commit private data or credentials. The initial skeleton has no external
service calls and does not implement answer verification or access control.
