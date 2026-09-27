import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_retrieval.models import Document
from adaptive_retrieval.retrieval import KeywordRetriever


class KeywordRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.retriever = KeywordRetriever([
            Document("a", "Reset your password", "synthetic://a"),
            Document("b", "Password requirements", "synthetic://b"),
            Document("c", "VPN connection", "synthetic://c"),
        ])

    def test_ranks_relevant_documents_and_preserves_sources(self):
        results = self.retriever.search("RESET password!", top_k=1)
        self.assertEqual([item.document.id for item in results], ["a"])
        self.assertEqual(results[0].document.source, "synthetic://a")

    def test_unmatched_and_empty_queries_return_no_evidence(self):
        for query in ["", "?!", "payroll"]:
            with self.subTest(query=query):
                self.assertEqual(self.retriever.search(query), [])

    def test_invalid_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            self.retriever.search("password", top_k=0)


if __name__ == "__main__":
    unittest.main()
