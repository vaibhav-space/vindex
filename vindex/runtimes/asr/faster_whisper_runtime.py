from pathlib import Path
from typing import Any, Optional

from faster_whisper import WhisperModel

from vindex.core.interfaces.runtimes import ASRRuntime


class FasterWhisperRuntime(ASRRuntime):
    """ASR runtime using faster-whisper (CTranslate2)."""

    def __init__(self) -> None:
        self.model: Optional[WhisperModel] = None
        self.loaded_path: Optional[Path] = None

    def load(self, model_dir_or_path: Path) -> None:
        """Load model weights locally into memory."""
        if self.model is not None and self.loaded_path == model_dir_or_path:
            return  # Already loaded
            
        if not model_dir_or_path.is_dir() or not (model_dir_or_path / "model.bin").exists():
            raise FileNotFoundError(
                f"CTranslate2 model weights not found at: {model_dir_or_path}. "
                "Please download the weights and configure the local path. "
                "Auto-downloads are prohibited."
            )
        
        # Hardcode default safe options for local Macbook Air
        self.model = WhisperModel(str(model_dir_or_path), device="cpu", compute_type="int8")
        self.loaded_path = model_dir_or_path

    def unload(self) -> None:
        """Unload model weights and clear GPU/CPU cache."""
        self.model = None
        self.loaded_path = None

    def transcribe(self, audio_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Transcribe audio to word-level timestamped segments."""
        model_dir_str = config.get("model_dir")
        if not model_dir_str:
            raise ValueError(
                "FasterWhisperRuntime requires 'model_dir' to be set in the config."
            )

        model_path = Path(model_dir_str)
        self.load(model_path)

        if self.model is None:
            raise RuntimeError("FasterWhisper model was not loaded successfully.")

        # Transcribe with word-level timestamps, deterministic settings
        segments, _ = self.model.transcribe(
            str(audio_path),
            word_timestamps=True,
            beam_size=config.get("beam_size", 1),
            temperature=config.get("temperature", 0.0),
            language=config.get("language"),
            task=config.get("task", "transcribe"),
        )


        words_list = []
        for segment in segments:
            if segment.words:
                for w in segment.words:
                    words_list.append({
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "confidence": w.probability,
                    })
        return words_list

    @property
    def runtime_id(self) -> str:
        return "faster_whisper.v1"

