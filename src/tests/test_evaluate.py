import sys
from pathlib import Path
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptive_retrieval.evaluate import evaluate_question, grouped_metrics, summarize_records


class FakeSession:
    rows = [1, 2, 3]

    def search(self, question, top_k):
        return [(SimpleNamespace(document_id=doc, id=str(i)), 1 - i / 10)
                for i, doc in enumerate(["wrong", "wrong", "gold"])]


class EvaluationTests(unittest.TestCase):
    def question(self, gold):
        return {"question_id": "q", "question": "test", "expected_doc_ids": gold,
                "split": "dev", "question_type": "basic"}

    def test_multiple_chunks_do_not_inflate_document_rank(self):
        result = evaluate_question(FakeSession(), self.question(["gold"]))
        self.assertEqual(result["gold_rank"], 2)
        self.assertEqual(result["reciprocal_rank"], .5)
        self.assertEqual(result["hit@1"], 0)
        self.assertEqual(result["hit@5"], 1)

    def test_unanswerable_is_not_scored_as_retrieval_failure(self):
        result = evaluate_question(FakeSession(), self.question([]))
        self.assertIsNone(result["hit@5"])
        summary = summarize_records([result])
        self.assertEqual(summary["unscored"], 1)
        self.assertIsNone(summary["mrr"])

    def test_missing_gold_is_zero_and_groups_are_separate(self):
        hit = evaluate_question(FakeSession(), self.question(["gold"]))
        miss = evaluate_question(FakeSession(), self.question(["missing"]))
        miss["split"] = "test"
        summary = summarize_records([hit, miss])
        self.assertEqual(summary["hit@5"], .5)
        self.assertEqual(summary["mrr"], .25)
        self.assertEqual(grouped_metrics([hit, miss], "split")["test"]["mrr"], 0)

    def test_empty_summary(self):
        self.assertIsNone(summarize_records([])["p95_retrieval_latency_ms"])
        self.assertEqual(grouped_metrics([], "split"), {})


if __name__ == "__main__":
    unittest.main()
