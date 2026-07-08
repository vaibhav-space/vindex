from pathlib import Path
from typing import Any, Optional

from vindex.core.interfaces.runtimes import SemanticEmbeddingRuntime


class MiniLMEmbeddingRuntime(SemanticEmbeddingRuntime):
    """Text embedding runtime using sentence-transformers (all-MiniLM-L6-v2)."""

    def __init__(self) -> None:
        self.model: Any = None
        self.loaded_model_dir: Optional[Path] = None

    def load(self, model_dir_or_path: Path) -> None:
        """Load model weights locally into memory."""
        if self.model is not None and self.loaded_model_dir == model_dir_or_path:
            return  # Already loaded

        if not model_dir_or_path.is_dir() or not (model_dir_or_path / "config.json").exists():
            raise FileNotFoundError(
                f"SentenceTransformer model weights not found at: {model_dir_or_path}. "
                "Please download the weights locally. Auto-downloads are prohibited."
            )

        from sentence_transformers import SentenceTransformer
        # Enforce local_files_only=True to prevent implicit network calls
        self.model = SentenceTransformer(str(model_dir_or_path), local_files_only=True)
        self.loaded_model_dir = model_dir_or_path

    def unload(self) -> None:
        """Unload weights and clear sentence-transformers model instance."""
        self.model = None
        self.loaded_model_dir = None

    def embed_text(self, texts: list[str], config: dict[str, Any]) -> list[list[float]]:
        """Embed list of texts into dense vectors."""
        model_dir_str = config.get("model_dir")
        if not model_dir_str:
            raise ValueError(
                "MiniLMEmbeddingRuntime requires 'model_dir' to be configured."
            )

        model_path = Path(model_dir_str)
        self.load(model_path)

        if self.model is None:
            raise RuntimeError("SentenceTransformer model was not loaded successfully.")

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Convert numpy array to list of list of floats
        return [list(map(float, vec)) for vec in embeddings]

    @property
    def runtime_id(self) -> str:
        return "sentence_transformers.minilm.v1"

