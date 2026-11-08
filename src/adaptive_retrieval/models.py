"""Shared contracts; model scores are not evidence verification."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    source: str
    path: str | None = None


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    text: str
    source: str
    path: str | None
    start_char: int
    end_char: int


@dataclass(frozen=True)
class Evidence:
    document: Document
    score: float


@dataclass(frozen=True)
class Answer:
    text: str
    citations: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalResult:
    answer: Answer | None
    route: Literal["cache", "single_pass", "second_pass", "refusal"]
    evidence: tuple[Evidence, ...]
    retrieval_rounds: int
    latency_ms: float
    # None means unmeasured, rather than a claim of zero cost.
    cost_usd: float | None = None
