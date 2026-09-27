"""Minimal lexical overlap demo, not BM25 or a production retrieval system."""

import re

from .models import Document, Evidence


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold()))


class KeywordRetriever:
    def __init__(self, documents: list[Document]) -> None:
        self._documents = tuple(documents)

    def search(self, question: str, top_k: int = 3) -> list[Evidence]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        query = _tokens(question)
        if not query:
            return []
        results = [
            Evidence(document, len(query & _tokens(document.text)) / len(query))
            for document in self._documents
        ]
        return sorted(
            (item for item in results if item.score > 0),
            key=lambda item: (-item.score, item.document.id),
        )[:top_k]
