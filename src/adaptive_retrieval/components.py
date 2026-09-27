"""Interfaces for parallel team development; implementations are future work."""

from typing import Protocol

from .models import Answer, Evidence


class Retriever(Protocol):
    def search(self, question: str, top_k: int = 3) -> list[Evidence]: ...


class Reranker(Protocol):
    def rerank(self, question: str, evidence: list[Evidence]) -> list[Evidence]: ...


class EvidenceChecker(Protocol):
    def is_sufficient(self, question: str, evidence: list[Evidence]) -> bool: ...


class QueryRewriter(Protocol):
    def rewrite(self, question: str, evidence: list[Evidence]) -> str: ...


class Generator(Protocol):
    def generate(self, question: str, evidence: list[Evidence]) -> Answer: ...


class VerifiedCache(Protocol):
    """Implementations must isolate contexts and invalidate stale corpus entries."""

    def lookup(
        self, question: str, context_id: str, corpus_version: str
    ) -> Answer | None: ...
