"""Run from any directory with Python 3.11+, without installation or API keys."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adaptive_retrieval.models import Document
from adaptive_retrieval.retrieval import KeywordRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline keyword retrieval demo")
    parser.add_argument("question", nargs="?", default="reset password")
    args = parser.parse_args()
    records = json.loads((ROOT / "data/sample/documents.json").read_text(encoding="utf-8"))
    results = KeywordRetriever([Document(**record) for record in records]).search(args.question)
    print("Synthetic keyword-search demo (no generated answer)")
    for item in results:
        print(f"{item.document.id} | overlap={item.score:.2f} | {item.document.source}")
        print(item.document.text)
    if not results:
        print("No matching evidence found.")


if __name__ == "__main__":
    main()
