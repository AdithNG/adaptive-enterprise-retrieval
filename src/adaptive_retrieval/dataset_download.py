"""Recreate the pinned 100-question subset from upstream release assets."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

from .paths import DATA_DIR, SUBSET_DOCUMENTS_DIR


RELEASE_BASE = (
    "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/"
    "releases/download/v1.0.0"
)
MANIFEST_PATH = DATA_DIR / "subset_manifest.json"
RAW_DIR = DATA_DIR / "raw"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download_asset(name: str, expected_sha: str, destination: Path) -> None:
    """Download once, resume a partial download, and verify before using it."""
    if destination.is_file():
        if sha256(destination) != expected_sha:
            raise ValueError(f"Existing download has the wrong checksum: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".partial")
    offset = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "adaptive-enterprise-retrieval/0.1"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = Request(f"{RELEASE_BASE}/{name}", headers=headers)
    print(f"Downloading {name} from EnterpriseRAG-Bench v1.0.0...", flush=True)
    try:
        response = urlopen(request, timeout=60)
    except HTTPError as exc:
        if exc.code == 416 and sha256(partial) == expected_sha:
            os.replace(partial, destination)
            return
        raise
    with response:
        # Some servers ignore Range. In that case restart the partial file.
        resumed = offset and response.status == 206
        with partial.open("ab" if resumed else "wb") as stream:
            downloaded = offset if resumed else 0
            next_report = ((downloaded // (100 * 1024 * 1024)) + 1) * 100 * 1024 * 1024
            while block := response.read(1024 * 1024):
                stream.write(block)
                downloaded += len(block)
                if downloaded >= next_report:
                    print(f"  {downloaded / (1024 * 1024):.0f} MiB", flush=True)
                    next_report += 100 * 1024 * 1024
    if sha256(partial) != expected_sha:
        raise ValueError(f"Download checksum mismatch: {partial}")
    os.replace(partial, destination)


def _document_path(relative: str) -> Path:
    path = PurePosixPath(relative)
    if (
        path.is_absolute() or ".." in path.parts or len(path.parts) < 2
        or path.suffix != ".txt" or not path.name.startswith("dsid_")
    ):
        raise ValueError(f"Unsafe document path in subset manifest: {relative}")
    return Path(*path.parts)


def _selected_questions(full_questions: Path, manifest: dict) -> bytes:
    if sha256(full_questions) != manifest["questions_sha256"]:
        raise ValueError("The upstream question file differs from the pinned release")
    records = [json.loads(line) for line in full_questions.read_text(encoding="utf-8").splitlines()]
    by_id = {record["question_id"]: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("Duplicate question IDs in upstream question file")
    lines = []
    for selection in manifest["questions"]:
        question_id = selection["question_id"]
        if question_id not in by_id:
            raise ValueError(f"Question {question_id} is absent from the pinned release")
        row = {**by_id[question_id], "split": selection["split"]}
        row["hard_negative_ids"] = selection["hard_negative_ids"]
        lines.append(json.dumps(row) + "\n")
    result = "".join(lines).encode("utf-8")
    if hashlib.sha256(result).hexdigest() != manifest["subset_questions_sha256"]:
        raise ValueError("Rebuilt question subset does not match the saved selection")
    return result


def _required_documents(manifest: dict, questions: bytes) -> dict[str, tuple[Path, str]]:
    required = set()
    for line in questions.splitlines():
        row = json.loads(line)
        required.update(row["expected_doc_ids"])
        required.update(row["hard_negative_ids"])
    documents = {}
    for item in manifest["documents"]:
        path = _document_path(item["path"])
        doc_id = path.name.split("__", 1)[0]
        if doc_id in documents:
            raise ValueError(f"Duplicate document ID in subset manifest: {doc_id}")
        documents[doc_id] = (path, item["sha256"])
    if set(documents) != required:
        raise ValueError("Subset manifest documents do not match the selected questions")
    return documents


def _local_subset_ready(root: Path, manifest: dict) -> bool:
    questions = root / "questions_100.jsonl"
    ready = True
    if questions.exists():
        if sha256(questions) != manifest["subset_questions_sha256"]:
            raise ValueError(f"Existing question subset differs: {questions}")
        _required_documents(manifest, questions.read_bytes())
    else:
        ready = False
    for item in manifest["documents"]:
        target = root / _document_path(item["path"])
        if target.exists():
            if sha256(target) != item["sha256"]:
                raise ValueError(f"Existing document differs: {target}")
        else:
            ready = False
    return ready


def materialize_subset(
    full_questions: Path, archive_path: Path, root: Path, manifest: dict,
) -> None:
    """Validate all content before writing the selected documents locally."""
    questions = _selected_questions(full_questions, manifest)
    documents = _required_documents(manifest, questions)
    if sha256(archive_path) != manifest["archive_sha256"]:
        raise ValueError("The document archive differs from the pinned release")
    contents = {}
    with ZipFile(archive_path) as archive:
        for doc_id, (path, expected_sha) in documents.items():
            # The official archive uses source-type folders at its top level.
            name = path.as_posix()
            try:
                data = archive.read(name)
            except KeyError as exc:
                raise ValueError(f"Document {doc_id} is absent from the release archive: {name}") from exc
            if hashlib.sha256(data).hexdigest() != expected_sha:
                raise ValueError(f"Document {doc_id} differs from the pinned subset")
            contents[path] = data
    question_target = root / "questions_100.jsonl"
    if question_target.exists() and question_target.read_bytes() != questions:
        raise ValueError(f"Existing question subset differs: {question_target}")
    for path, data in contents.items():
        target = root / path
        if target.exists() and target.read_bytes() != data:
            raise ValueError(f"Existing document differs: {target}")
    root.mkdir(parents=True, exist_ok=True)
    if not question_target.exists():
        question_target.write_bytes(questions)
    for path, data in contents.items():
        target = root / path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def ensure_subset_data(
    root: Path = SUBSET_DOCUMENTS_DIR, manifest_path: Path = MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
) -> dict:
    """Use valid local files or download pinned release assets once per device."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if _local_subset_ready(root, manifest):
        print("Dataset subset already available locally; no download needed.")
        return manifest
    questions = raw_dir / "questions_v1.0.0.jsonl"
    archive = raw_dir / "all_documents_v1.0.0.zip"
    _download_asset("questions.jsonl", manifest["questions_sha256"], questions)
    _download_asset("all_documents.zip", manifest["archive_sha256"], archive)
    materialize_subset(questions, archive, root, manifest)
    print(f"Prepared local source subset: {len(manifest['questions'])} questions, "
          f"{len(manifest['documents'])} documents in {root}")
    return manifest
