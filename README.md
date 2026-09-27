# Cost-Aware Adaptive Retrieval for Enterprise Support

Team 13's project investigates whether adaptive retrieval can reduce response
time and cost while preserving answer quality on enterprise support questions.
The source proposal is [included in this repository](<Cost-Aware Adaptive Agentic Retrieval for Enterprise Support (2).pdf>).

## Current status

This is a starter skeleton, with shared data contracts, component interfaces,
an offline keyword-search demo, tests, and CI. The adaptive agent, reranker,
model integration, benchmark loader, and evaluation runner are planned work.
Demo results are synthetic search results, not generated answers or benchmark findings.

## Quick start

Use Python 3.11 or newer. From the repository root, these commands work in
PowerShell, macOS, and Linux without installing dependencies or using API keys:

```sh
python scripts/demo.py
python scripts/demo.py "reset password"
python -m unittest discover -s tests -v
```

For development, optionally create a virtual environment and install the package:

```sh
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in PowerShell or
`source .venv/bin/activate` on macOS/Linux, then run `python -m pip install -e .`.

## Planned pipeline

Question → verified cache lookup → keyword retrieval → reranking → evidence check
→ grounded answer or one rewritten retrieval attempt → answer or explicit refusal.

The cache will need question, context, and corpus-version checks. A retrieval
score alone must not be treated as proof that an answer is supported.

## Repository layout

| Path | Purpose |
| --- | --- |
| `docs/PLAN.md` | Ten-week milestones, six workstreams, evaluation protocol |
| `src/adaptive_retrieval/models.py` | Shared document, evidence, and result types |
| `src/adaptive_retrieval/components.py` | Interfaces for future pipeline components |
| `src/adaptive_retrieval/retrieval.py` | Small in-memory keyword baseline for the demo |
| `data/sample/` | Synthetic, shareable demo documents |
| `data/raw/`, `data/processed/` | Local datasets and derived artifacts (ignored) |
| `scripts/demo.py` | Offline search entry point |
| `tests/` | Behavioral tests |
| `outputs/` | Local experiment outputs (ignored) |

## Working as a team

See [the project plan](docs/PLAN.md) for suggested ownership and
[CONTRIBUTING.md](CONTRIBUTING.md) for the branch and pull-request workflow.
Assign actual teammates to the six workstreams together. Keep API keys, private
company documents, and downloaded benchmark artifacts out of Git.

The benchmark target is a manageable ONYX EnterpriseRAG-Bench subset with at
least approximately 300 questions and a 70/15/15 development/validation/test
split. Dataset access and reuse terms still need verification. No dataset or
model provider has been integrated yet.
