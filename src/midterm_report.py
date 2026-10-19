"""Build a presentation evidence brief from saved results; no model calls."""

import argparse
import json
from pathlib import Path

from adaptive_retrieval.data import load_documents
from adaptive_retrieval.evaluate import grouped_metrics, summarize_records
from adaptive_retrieval.vector_index import file_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--corpus", type=Path, default=Path("data/processed/subset_corpus.jsonl"))
    args = parser.parse_args()
    records = [json.loads(line) for line in (args.run / "per_question.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = json.loads((args.run / "summary.json").read_text(encoding="utf-8"))
    if file_sha256(args.corpus) != summary["run"]["index"]["corpus_sha256"]:
        parser.error("Corpus differs from the evaluated corpus; use the original corpus for examples.")
    docs = {doc.id: doc for doc in load_documents(args.corpus)}
    overall = summarize_records(records)
    lines = ["# Midterm evidence brief", "", 
             "Exploratory retrieval baseline, not answer-quality or adaptive-system results.", "",
             f"Corpus: {len(docs)} documents. Questions: {len(records)}; scored: {overall['scored']}.",
             f"Code commit: {summary['run']['git_commit']}", "",
             "## Retrieval metrics", "",
             "| Group | Scored | Hit@1 | Hit@5 | MRR |", "| --- | ---: | ---: | ---: | ---: |"]
    groups = {"All (pooled)": overall}
    groups.update({f"Split: {k}": v for k, v in grouped_metrics(records, "split").items()})
    groups.update({f"Type: {k}": v for k, v in grouped_metrics(records, "question_type").items()})
    for key, value in groups.items():
        metrics = [f"{value[m]:.3f}" if value[m] is not None else "N/A" for m in ["hit@1", "hit@5", "mrr"]]
        lines.append(f"| {key} | {value['scored']} | " + " | ".join(metrics) + " |")
    lines += ["", "## Examples for manual review", "",
              "Selected deterministically from development questions only. These demonstrate document retrieval, not verified generated answers."]
    candidates = [r for r in records if r.get("split") == "dev" and r["answerable"]]
    selections = [
        ("Rank-one success", next((r for r in candidates if r["gold_rank"] == 1), None)),
        ("Semantic miss outside top five", next((r for r in candidates if r.get("question_type") == "semantic" and not r["hit@5"]), None)),
    ]
    examples = []
    for label, record in selections:
        if record is None:
            continue
        example = {"label": label, **record, "gold_documents": [
            {"id": doc_id, "source": docs[doc_id].source, "text": docs[doc_id].text}
            for doc_id in record["expected_doc_ids"] if doc_id in docs]}
        examples.append(example)
        lines += ["", f"### {label}", "", f"Question ({record['question_id']}): {record['question']}",
                  "", f"Gold document rank: {record['gold_rank']}. Gold IDs: {', '.join(record['expected_doc_ids'])}.",
                  "", "Top retrieved document: " + record["retrieved"][0]["doc_id"]]
    lines += ["", "## Limits and next steps", "",
              "- No multi-document gold questions in the current subset; add them before claiming that capability.",
              "- Ten info-not-found questions are unscored for retrieval; refusal behavior has not been implemented or evaluated.",
              "- Split metrics are descriptive. Earlier pooled results have already been inspected; do not present this as a pristine held-out study.",
              "- MRR averages reciprocal rank, not rank. Retrieval success does not prove answer correctness.",
              "- This local baseline has no paid generation calls; zero API spend does not mean zero compute cost.",
              "- Next: grounded generation/refusal, reranking, verified cache and bounded second retrieval, followed by quality/latency/cost comparisons.", ""]
    (args.run / "MIDTERM_BRIEF.md").write_text("\n".join(lines), encoding="utf-8")
    (args.run / "examples.json").write_text(json.dumps(examples, indent=2) + "\n", encoding="utf-8")
    print(args.run / "MIDTERM_BRIEF.md")


if __name__ == "__main__":
    main()
