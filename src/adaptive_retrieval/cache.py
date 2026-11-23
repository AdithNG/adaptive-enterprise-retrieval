"""Verified-answer cache: reuse a stored answer only for the same question.

Lookup has two steps. Cosine similarity of question embeddings finds candidate
cached questions; it cannot decide reuse on its own, because a near-miss ("error
rate threshold" vs "latency threshold" in the same runbook) scores as high as a
true paraphrase. An NLI model then has to judge the two questions as entailing
each other in both directions before the stored answer is reused.

Entries are keyed by context and corpus version, so other contexts never match
and a corpus change makes old answers unreachable. Store only answers that
passed verification; the cache repeats whatever it is given.
"""

import math
import re
from collections.abc import Sequence
from typing import Protocol

from .models import Answer


class QuestionEmbedder(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]: ...


class EntailmentJudge(Protocol):
    def assess(self, premise: str, hypothesis: str) -> dict: ...


def _normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question).strip().casefold()


def _unit(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


class NliVerifiedCache:
    def __init__(
        self, embedder: QuestionEmbedder, judge: EntailmentJudge, *,
        candidate_threshold: float = 0.70, nli_threshold: float = 0.5,
        max_candidates: int = 3,
    ) -> None:
        if not 0 <= candidate_threshold <= 1 or not 0 < nli_threshold < 1 or max_candidates < 1:
            raise ValueError("Invalid cache thresholds")
        self.embedder, self.judge = embedder, judge
        self.candidate_threshold = candidate_threshold
        self.nli_threshold = nli_threshold
        self.max_candidates = max_candidates
        # (context_id, corpus_version) -> list of (normalized question, question, unit vector, answer)
        self._entries: dict[tuple[str, str], list[tuple[str, str, list[float], Answer]]] = {}
        self.last_decision: dict = {}

    def __len__(self) -> int:
        return sum(len(rows) for rows in self._entries.values())

    def store(self, question: str, answer: Answer, context_id: str, corpus_version: str) -> None:
        if not question.strip():
            raise ValueError("Cannot cache an empty question")
        vector = _unit(self.embedder.embed_texts([question])[0])
        self._entries.setdefault((context_id, corpus_version), []).append(
            (_normalize(question), question, vector, answer))

    def mutual_entailment(self, a: str, b: str) -> float:
        return min(self.judge.assess(a, b)["max_entailment"],
                   self.judge.assess(b, a)["max_entailment"])

    def lookup(self, question: str, context_id: str, corpus_version: str) -> Answer | None:
        rows = self._entries.get((context_id, corpus_version), [])
        self.last_decision = {"hit": False, "reason": "empty", "candidates": []}
        if not rows:
            return None
        key = _normalize(question)
        for normalized, cached_q, _, answer in rows:
            if normalized == key:
                self.last_decision = {"hit": True, "reason": "exact", "matched": cached_q}
                return answer
        query = _unit(self.embedder.embed_texts([question])[0])
        scored = sorted(((sum(a * b for a, b in zip(query, vector)), cached_q, answer)
                         for _, cached_q, vector, answer in rows),
                        key=lambda row: row[0], reverse=True)
        candidates = [row for row in scored[:self.max_candidates]
                      if row[0] >= self.candidate_threshold]
        self.last_decision["reason"] = "no candidate" if not candidates else "nli rejected"
        for cosine, cached_q, answer in candidates:
            entailment = self.mutual_entailment(question, cached_q)
            self.last_decision["candidates"].append(
                {"question": cached_q, "cosine": cosine, "entailment": entailment})
            if entailment >= self.nli_threshold:
                self.last_decision.update(hit=True, reason="nli", matched=cached_q)
                return answer
        return None
