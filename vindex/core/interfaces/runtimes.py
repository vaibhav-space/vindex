from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class RuntimePlugin(ABC):
    """Base interface for all pluggable perception engine runtimes (v2.0)."""

    @abstractmethod
    def load(self, model_dir_or_path: Path) -> None:
        """Load model weights/binaries into memory."""
        ...

    @abstractmethod
    def unload(self) -> None:
        """Unload model weights and free device/system memory resources."""
        ...

    @property
    @abstractmethod
    def runtime_id(self) -> str:
        """Stable identifier for the runtime implementation."""
        ...


class ASRRuntime(RuntimePlugin):
    """Transcribes audio to word-level timestamped output."""

    @abstractmethod
    def transcribe(self, audio_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Transcribe audio file.
        
        Returns:
            list[dict]: [{"word": str, "start": float, "end": float, "confidence": float}]
        """
        ...


class OCRRuntime(RuntimePlugin):
    """Extracts text regions from a single image frame."""

    @abstractmethod
    def extract_text(self, frame_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract text from frame.
        
        Returns:
            list[dict]: [{"text": str, "bbox": [x, y, w, h], "confidence": float}]
        """
        ...


class SceneUnderstandingRuntime(RuntimePlugin):
    """Generates natural language description for frames/scenes (visual only)."""

    @abstractmethod
    def describe_scene(self, frame_paths: list[Path], prompt: str, config: dict[str, Any]) -> str:
        """Describe visual content of keyframes given a prompt."""
        ...


class ObjectDetectionRuntime(RuntimePlugin):
    """Detects bounding boxes of specific visual object classes (e.g. YOLO)."""

    @abstractmethod
    def detect_objects(self, frame_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Detect objects inside image frame.
        
        Returns:
            list[dict]: [{"label": str, "bbox": [x, y, w, h], "confidence": float}]
        """
        ...


class VisualEmbeddingRuntime(RuntimePlugin):
    """Generates visual embeddings from image frames."""

    @abstractmethod
    def embed_image(self, frame_path: Path, config: dict[str, Any]) -> list[float]:
        """Embed a single frame."""
        ...


class SemanticEmbeddingRuntime(RuntimePlugin):
    """Generates semantic text embeddings (e.g. MiniLM)."""

    @abstractmethod
    def embed_text(self, texts: list[str], config: dict[str, Any]) -> list[list[float]]:
        """Embed text segments."""
        ...


class AudioEventRuntime(RuntimePlugin):
    """Identifies specific audio events / sound classifications (e.g. YAMNet)."""

    @abstractmethod
    def detect_audio_events(self, audio_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Classify audio events.
        
        Returns:
            list[dict]: [{"label": str, "start_ms": int, "end_ms": int, "confidence": float}]
        """
        ...


class MotionAnalysisRuntime(RuntimePlugin):
    """Analyzes pixel differences or optical flows (math or lightweight ML)."""

    @abstractmethod
    def analyze_motion(self, frame_paths: list[Path], config: dict[str, Any]) -> dict[str, Any]:
        """Analyze motion between sequence of keyframes."""
        ...


class LLMRuntime(RuntimePlugin):
    """Generates markdown text from narration prompt."""

    @abstractmethod
    def generate(self, prompt: str, config: dict[str, Any]) -> str:
        """Generate narrative text."""
        ...

