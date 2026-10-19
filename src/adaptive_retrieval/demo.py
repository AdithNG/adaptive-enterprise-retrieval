"""Synthetic keyword-search demo, without installation or API keys."""

import argparse
import json
from .models import Document
from .paths import SAMPLE_DOCUMENTS
from .retrieval import KeywordRetriever


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Offline keyword retrieval demo")
    parser.add_argument("question", nargs="?", default="reset password")
    args = parser.parse_args(argv)
    records = json.loads(SAMPLE_DOCUMENTS.read_text(encoding="utf-8"))
    results = KeywordRetriever([Document(**record) for record in records]).search(args.question)
    print("Synthetic keyword-search demo (no generated answer)")
    for item in results:
        print(f"{item.document.id} | overlap={item.score:.2f} | {item.document.source}")
        print(item.document.text)
    if not results:
        print("No matching evidence found.")


if __name__ == "__main__":
    main()
