"""Embedding adapter; model downloads and inference happen only when requested."""

from collections.abc import Sequence
from typing import Protocol

from .paths import PROCESSED_DIR


MINILM_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder(Protocol):
    model_name: str

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]: ...


class MiniLMEmbedder:
    """Local sentence-transformers encoder used for both chunks and queries."""

    model_name = MINILM_MODEL

    def __init__(self, batch_size: int = 32) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self.batch_size = batch_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "Local embeddings need sentence-transformers. "
                    "Install with: python -m pip install -e '.[local-embeddings]'"
                ) from exc
            cache_dir = PROCESSED_DIR / "models"
            cache_dir.mkdir(parents=True, exist_ok=True)
            snapshots = cache_dir / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots"
            cached = snapshots.is_dir() and any(snapshots.glob("*/modules.json"))
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=str(cache_dir),
                local_files_only=bool(cached),
            )
        return self._model

    @property
    def tokenizer(self):
        return self._load_model().tokenizer

    @property
    def max_input_tokens(self) -> int:
        return self._load_model().max_seq_length

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Every embedding input must be non-empty text")
        model = self._load_model()
        max_tokens = model.max_seq_length
        for index, text in enumerate(texts):
            token_count = len(model.tokenizer.encode(text, add_special_tokens=True))
            if token_count > max_tokens:
                raise ValueError(
                    f"Input {index} has {token_count} model tokens, above the {max_tokens} "
                    "token limit. Rebuild with a smaller --max-words value."
                )
        vectors = model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]
