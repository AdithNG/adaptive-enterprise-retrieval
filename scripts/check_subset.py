"""Check that the subset corpus contains every document its questions reference.

For each question in subset_questions.jsonl, every expected (gold) doc id and
every hard negative id must be present both in subset_corpus.jsonl and as a
file under data/subset_documents/. Also reports documents nobody references.

Usage: python scripts/check_subset.py
"""

import json
import sys
from pathlib import Path

QUESTIONS = Path("data/processed/subset_questions.jsonl")
CORPUS = Path("data/processed/subset_corpus.jsonl")
DOCS_DIR = Path("data/subset_documents")


def main():
    questions = [json.loads(l) for l in open(QUESTIONS)]
    corpus = {d["doc_id"]: d for d in map(json.loads, open(CORPUS))}
    files = {p.name.split("__", 1)[0]: p for p in DOCS_DIR.rglob("*.txt")}

    errors = []
    referenced = set()
    for q in questions:
        for kind in ("expected_doc_ids", "hard_negative_ids"):
            for doc_id in q[kind]:
                referenced.add(doc_id)
                if doc_id not in corpus:
                    errors.append(
                        f"{q['question_id']}: {kind} {doc_id} missing from {CORPUS}"
                    )
                if doc_id not in files:
                    errors.append(
                        f"{q['question_id']}: {kind} {doc_id} missing from {DOCS_DIR}"
                    )
        if q["question_type"] != "info_not_found" and not q["expected_doc_ids"]:
            errors.append(f"{q['question_id']}: no expected_doc_ids")

    for doc_id, doc in corpus.items():
        if (
            doc_id in files
            and files[doc_id].read_text(encoding="utf-8", errors="ignore")
            != doc["text"]
        ):
            errors.append(f"{doc_id}: text in {CORPUS} differs from {files[doc_id]}")

    gold = {d for q in questions for d in q["expected_doc_ids"]}
    print(f"questions:           {len(questions)}")
    print(f"gold docs referenced: {len(gold)}")
    print(f"all docs referenced:  {len(referenced)}")
    print(f"docs in corpus jsonl: {len(corpus)}")
    print(f"docs in {DOCS_DIR}: {len(files)}")
    for label, extra in (
        ("corpus jsonl", corpus.keys() - referenced),
        (str(DOCS_DIR), files.keys() - referenced),
    ):
        if extra:
            print(
                f"note: {len(extra)} unreferenced docs in {label}: {sorted(extra)[:5]}"
            )

    if errors:
        print(f"\nFAILED: {len(errors)} problems")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    print("\nOK: every referenced document is present")


if __name__ == "__main__":
    main()
