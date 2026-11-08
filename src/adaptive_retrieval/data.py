"""Parse the evaluation corpus into the project's Document contract."""

import json
from pathlib import Path

from .models import Document
from .paths import PROCESSED_DIR


DEFAULT_CORPUS = PROCESSED_DIR / "subset_corpus.jsonl"


def load_documents(corpus_path: Path = DEFAULT_CORPUS) -> list[Document]:
    """Load one JSON object per line, preserving benchmark IDs and source paths."""
    corpus_path = Path(corpus_path)
    if not corpus_path.is_file():
        raise FileNotFoundError(
            f"Corpus not found: {corpus_path}. Run 'python src/runner.py build-subset' first."
        )

    documents: list[Document] = []
    seen: set[str] = set()
    with corpus_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                doc_id = record["doc_id"]
                text = record["text"]
                source = record["source"]
                relative_path = record.get("path")
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(f"Invalid corpus record at {corpus_path}:{line_number}") from exc
            if not all(isinstance(value, str) and value for value in (doc_id, text, source)):
                raise ValueError(f"Empty or non-text field at {corpus_path}:{line_number}")
            if relative_path is not None and not isinstance(relative_path, str):
                raise ValueError(f"Invalid path at {corpus_path}:{line_number}")
            if doc_id in seen:
                raise ValueError(f"Duplicate document ID {doc_id!r} at {corpus_path}:{line_number}")
            seen.add(doc_id)
            documents.append(Document(doc_id, text, source, relative_path))
    if not documents:
        raise ValueError(f"Corpus is empty: {corpus_path}")
    return documents
