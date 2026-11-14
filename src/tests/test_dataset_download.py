"""Dataset setup must reproduce the pinned subset without network on reruns."""

import hashlib
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptive_retrieval.dataset_download import ensure_subset_data, materialize_subset
from adaptive_retrieval.prepare_subset import prepare_subset


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class DatasetDownloadTests(unittest.TestCase):
    def fixture(self, directory: Path):
        raw, root = directory / "raw", directory / "subset"
        raw.mkdir()
        question = {
            "question_id": "q1", "question": "What is the policy?",
            "expected_doc_ids": ["dsid_gold"], "question_type": "basic",
        }
        full = (json.dumps(question) + "\n").encode()
        selected = (json.dumps({
            **question, "split": "dev", "hard_negative_ids": ["dsid_negative"],
        }) + "\n").encode()
        questions_path = raw / "questions.jsonl"
        questions_path.write_bytes(full)
        documents = {
            "wiki/dsid_gold__policy.txt": b"Gold policy text",
            "wiki/dsid_negative__other.txt": b"Other policy text",
        }
        archive_path = raw / "all_documents.zip"
        with ZipFile(archive_path, "w") as archive:
            for name, data in documents.items():
                archive.writestr(name, data)
        manifest = {
            "questions_sha256": digest(full),
            "archive_sha256": digest(archive_path.read_bytes()),
            "subset_questions_sha256": digest(selected),
            "questions": [{
                "question_id": "q1", "split": "dev",
                "hard_negative_ids": ["dsid_negative"],
            }],
            "documents": [
                {"path": name, "sha256": digest(data)}
                for name, data in documents.items()
            ],
        }
        return questions_path, archive_path, root, manifest, selected, documents

    def test_materialize_and_reuse_exact_subset(self):
        with TemporaryDirectory() as directory:
            questions, archive, root, manifest, selected, documents = self.fixture(Path(directory))
            materialize_subset(questions, archive, root, manifest)
            self.assertEqual((root / "questions_100.jsonl").read_bytes(), selected)
            for name, data in documents.items():
                self.assertEqual((root / name).read_bytes(), data)
            self.assertEqual(prepare_subset(root, Path(directory) / "processed"), (1, 2))
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            with patch("adaptive_retrieval.dataset_download._download_asset") as download:
                ensure_subset_data(root, manifest_path, Path(directory) / "unused")
                download.assert_not_called()

    def test_missing_subset_is_downloaded_then_reused(self):
        with TemporaryDirectory() as directory:
            questions, archive, root, manifest, selected, documents = self.fixture(Path(directory))
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))

            def supply_asset(name, expected_sha, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(questions if name == "questions.jsonl" else archive, destination)

            with patch("adaptive_retrieval.dataset_download._download_asset", side_effect=supply_asset) as download:
                ensure_subset_data(root, manifest_path, Path(directory) / "cache")
                self.assertEqual(download.call_count, 2)
                ensure_subset_data(root, manifest_path, Path(directory) / "cache")
                self.assertEqual(download.call_count, 2)
            self.assertEqual((root / "questions_100.jsonl").read_bytes(), selected)
            self.assertEqual({name: (root / name).read_bytes() for name in documents}, documents)

    def test_bad_archive_does_not_write_a_partial_subset(self):
        with TemporaryDirectory() as directory:
            questions, archive, root, manifest, _, _ = self.fixture(Path(directory))
            manifest["documents"][0]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "differs from the pinned subset"):
                materialize_subset(questions, archive, root, manifest)
            self.assertFalse(root.exists())

    def test_changed_local_document_fails_before_downloading(self):
        with TemporaryDirectory() as directory:
            questions, archive, root, manifest, _, documents = self.fixture(Path(directory))
            materialize_subset(questions, archive, root, manifest)
            (root / next(iter(documents))).write_text("Locally edited")
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            with patch("adaptive_retrieval.dataset_download._download_asset") as download:
                with self.assertRaisesRegex(ValueError, "Existing document differs"):
                    ensure_subset_data(root, manifest_path, Path(directory) / "unused")
                download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
