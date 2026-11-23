import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptive_retrieval.cache import NliVerifiedCache
from adaptive_retrieval.models import Answer

VOCAB = ["latency", "error", "rate", "threshold", "escalation", "runbook", "p95", "sustained"]


class BagOfWords:
    def embed_texts(self, texts):
        return [[t.lower().count(w) for w in VOCAB] for t in texts]


class KeywordJudge:
    """Entails only when both questions ask about the same metric."""

    def __init__(self):
        self.calls = 0

    def assess(self, premise, hypothesis):
        self.calls += 1
        metric = lambda s: "error" if "error" in s.lower() else "latency"
        return {"max_entailment": 0.95 if metric(premise) == metric(hypothesis) else 0.01}


SEED = "What latency threshold in the runbook triggers escalation, and how long sustained?"
PARAPHRASE = "How long must P95 latency stay above the runbook threshold before escalation?"
NEAR_MISS = "What error rate threshold in the runbook triggers escalation, and how long sustained?"
ANSWER = Answer("P95 above 2000 ms for 10 minutes.", ("S1",))


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.judge = KeywordJudge()
        self.cache = NliVerifiedCache(BagOfWords(), self.judge, candidate_threshold=0.5)
        self.cache.store(SEED, ANSWER, "tenant-a", "v1")

    def test_paraphrase_reuses_answer(self):
        self.assertIs(self.cache.lookup(PARAPHRASE, "tenant-a", "v1"), ANSWER)
        self.assertEqual(self.cache.last_decision["reason"], "nli")

    def test_near_miss_is_rejected_despite_high_cosine(self):
        self.assertIsNone(self.cache.lookup(NEAR_MISS, "tenant-a", "v1"))
        candidate = self.cache.last_decision["candidates"][0]
        self.assertGreaterEqual(candidate["cosine"], 0.5)  # passed the cosine gate; NLI rejected it
        self.assertEqual(self.cache.last_decision["reason"], "nli rejected")

    def test_exact_repeat_skips_nli(self):
        self.assertIs(self.cache.lookup("  what LATENCY threshold in the runbook triggers "
                                        "escalation, and how long sustained? ", "tenant-a", "v1"), ANSWER)
        self.assertEqual(self.judge.calls, 0)

    def test_context_and_corpus_version_are_isolated(self):
        self.assertIsNone(self.cache.lookup(SEED, "tenant-b", "v1"))
        self.assertIsNone(self.cache.lookup(SEED, "tenant-a", "v2"))

    def test_unrelated_question_skips_nli(self):
        self.assertIsNone(self.cache.lookup("zzz", "tenant-a", "v1"))
        self.assertEqual(self.cache.last_decision["reason"], "no candidate")
        self.assertEqual(self.judge.calls, 0)

    def test_rejects_bad_settings(self):
        with self.assertRaises(ValueError):
            NliVerifiedCache(BagOfWords(), self.judge, nli_threshold=1.0)


if __name__ == "__main__":
    unittest.main()
