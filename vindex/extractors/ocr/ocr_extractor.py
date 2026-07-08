from pathlib import Path
from typing import Any, Iterator, Optional, cast

from vindex.core.interfaces.extractor import Extractor
from vindex.core.interfaces.runtimes import OCRRuntime
from vindex.core.schemas.observations import FrameObservation, OCRObservation


class OCRExtractor(Extractor):
    """Screen-text extraction (OCR) extractor."""

    def __init__(self, runtime: Optional[OCRRuntime] = None) -> None:
        self.runtime = runtime

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[OCRObservation]:
        """Extract text regions from the sampled keyframes of the video."""
        if self.runtime is None:
            raise ValueError("OCRExtractor requires an OCRRuntime injected during initialization.")

        frames = config.get("frames")
        if not frames:
            raise ValueError("OCRExtractor requires a list of 'frames' in the configuration dict.")

        # Ensure frame observations are correctly typed
        frame_list: list[FrameObservation] = []
        for f in frames:
            if isinstance(f, dict):
                frame_list.append(FrameObservation.model_validate(f))
            elif isinstance(f, FrameObservation):
                frame_list.append(f)
            else:
                raise TypeError(f"Invalid frame type in config: {type(f)}")

        for frame in frame_list:
            frame_path = Path(frame.frame_path)
            if not frame_path.exists():
                raise FileNotFoundError(f"Frame image not found: {frame_path}")

            # Run OCR runtime
            detections = self.runtime.extract_text(frame_path, config)

            for det in detections:
                text = str(det["text"])
                bbox = cast(list[float], det["bbox"])
                confidence = float(det.get("confidence", 1.0))

                yield OCRObservation(
                    schema_version="1.0",
                    timestamp_ms=frame.timestamp_ms,
                    source=self.extractor_id,
                    text=text,
                    bbox=bbox,
                    frame_ref=str(frame_path),
                    confidence=confidence,
                )

    @property
    def extractor_id(self) -> str:
        if self.runtime is not None:
            return f"ocr.runtime.{self.runtime.runtime_id}"
        return "ocr.unknown.v1"
