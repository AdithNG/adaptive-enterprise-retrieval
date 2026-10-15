"""Single command-line entry point for data preparation and retrieval."""

import argparse
from pathlib import Path

from adaptive_retrieval import build_subset, check_subset, demo, prepare_subset
from adaptive_retrieval.chunking import (
    chunk_documents, fit_chunks_to_token_limit, load_chunks, write_chunks,
)
from adaptive_retrieval.data import DEFAULT_CORPUS, load_documents
from adaptive_retrieval.embedding import MiniLMEmbedder
from adaptive_retrieval.interactive import SearchSession, run_interactive
from adaptive_retrieval.paths import FULL_DOCUMENTS_DIR, PROCESSED_DIR, SUBSET_DOCUMENTS_DIR
from adaptive_retrieval.vector_index import file_sha256, write_index


DEFAULT_CHUNKS = PROCESSED_DIR / "chunks.jsonl"
DEFAULT_INDEX = PROCESSED_DIR / "minilm_index.jsonl"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and search the enterprise retrieval subset")
    commands = parser.add_subparsers(dest="command", required=True)

    sample = commands.add_parser("demo", help="Search synthetic sample documents without a model")
    sample.add_argument("question", nargs="?", default="reset password")

    prepare = commands.add_parser("prepare-subset", help="Prepare the checked-in 100-question subset")
    prepare.add_argument("--root", type=Path, default=SUBSET_DOCUMENTS_DIR)
    prepare.add_argument("--out", type=Path, default=PROCESSED_DIR)

    build = commands.add_parser("build-subset", help="Select 100 questions from the full dataset")
    build.add_argument("--root", type=Path, default=FULL_DOCUMENTS_DIR)
    build.add_argument("--out", type=Path, default=PROCESSED_DIR)

    check = commands.add_parser("check-subset", help="Validate generated questions and documents")
    check.add_argument("--questions", type=Path, default=PROCESSED_DIR / "subset_questions.jsonl")
    check.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    check.add_argument("--docs-dir", type=Path, default=SUBSET_DOCUMENTS_DIR)

    chunk = commands.add_parser("chunk", help="Parse whole documents and write citation-ready chunks")
    chunk.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    chunk.add_argument("--out", type=Path, default=DEFAULT_CHUNKS)
    chunk.add_argument("--strategy", choices=("paragraph", "fixed"), default="paragraph")
    chunk.add_argument("--max-words", type=int, default=120)
    chunk.add_argument("--overlap-words", type=int, default=20)

    embed = commands.add_parser("embed", help="Encode chunks locally and save a searchable index")
    embed.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    embed.add_argument("--out", type=Path, default=DEFAULT_INDEX)
    embed.add_argument("--batch-size", type=int, default=32)

    search = commands.add_parser("search", help="Find relevant chunks; does not generate an answer")
    search.add_argument("question")
    search.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    search.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    search.add_argument("--top-k", type=int, default=5)

    interactive = commands.add_parser(
        "interactive", aliases=["chat"], help="Ask repeated questions and inspect source documents"
    )
    interactive.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    interactive.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    interactive.add_argument("--top-k", type=int, default=3)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            demo.main([args.question])
        elif args.command == "prepare-subset":
            prepare_subset.main(["--root", str(args.root), "--out", str(args.out)])
        elif args.command == "build-subset":
            build_subset.main(["--root", str(args.root), "--out", str(args.out)])
        elif args.command == "check-subset":
            check_subset.main([
                "--questions", str(args.questions), "--corpus", str(args.corpus),
                "--docs-dir", str(args.docs_dir),
            ])
        elif args.command == "chunk":
            documents = load_documents(args.corpus)
            chunks = chunk_documents(
                documents,
                strategy=args.strategy,
                max_words=args.max_words,
                overlap_words=args.overlap_words,
            )
            write_chunks(args.out, chunks, {
                "corpus_sha256": file_sha256(args.corpus),
                "strategy": args.strategy,
                "max_words": args.max_words,
                "overlap_words": args.overlap_words,
                "document_count": len(documents),
            })
            print(f"Parsed {len(documents)} documents into {len(chunks)} chunks: {args.out}")
        elif args.command == "embed":
            metadata, chunks = load_chunks(args.chunks)
            embedder = MiniLMEmbedder(batch_size=args.batch_size)
            fitted_chunks = fit_chunks_to_token_limit(
                chunks, embedder.tokenizer, embedder.max_input_tokens,
            )
            write_index(
                args.out, fitted_chunks, embedder,
                corpus_sha256=metadata["corpus_sha256"],
                strategy=metadata["strategy"],
                max_words=metadata["max_words"],
                overlap_words=metadata["overlap_words"],
                batch_size=args.batch_size,
            )
            print(
                f"Embedded {len(fitted_chunks)} model-safe pieces from {len(chunks)} "
                f"chunks with {embedder.model_name}: {args.out}"
            )
        elif args.command == "search":
            session = SearchSession(args.index, args.corpus)
            for chunk, score in session.search(args.question, args.top_k):
                source = chunk.path or chunk.source
                print(f"{chunk.id} | cosine={score:.3f} | {source} | chars {chunk.start_char}:{chunk.end_char}")
                print(chunk.text[:350].replace("\n", " "))
        elif args.command in {"interactive", "chat"}:
            session = SearchSession(args.index, args.corpus)
            run_interactive(session, args.top_k)
    except (FileNotFoundError, ValueError, RuntimeError, KeyError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
