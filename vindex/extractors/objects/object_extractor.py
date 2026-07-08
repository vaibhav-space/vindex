from pathlib import Path
from typing import Any, Iterator, Optional

from vindex.core.interfaces.extractor import Extractor
from vindex.core.interfaces.runtimes import ObjectDetectionRuntime
from vindex.core.schemas.observations import FrameObservation, ObjectObservation


class ObjectExtractor(Extractor):
    """Object detection extractor using a registered ObjectDetectionRuntime."""

    def __init__(self, runtime: Optional[ObjectDetectionRuntime] = None) -> None:
        self.runtime = runtime

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[ObjectObservation]:
        """Detect objects inside keyframe images."""
        if self.runtime is None:
            raise ValueError("ObjectExtractor requires an ObjectDetectionRuntime injected during initialization.")

        frames = config.get("frames")
        if not frames:
            raise ValueError("ObjectExtractor requires 'frames' in configuration.")

        # Parse frame observations
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
                continue

            # Run detection runtime
            detections = self.runtime.detect_objects(frame_path, config)

            # Deduce model info
            model_id = config.get("object_model_id", "yolov8n")
            model_version = config.get("object_model_version", "1.0")

            for det in detections:
                yield ObjectObservation(
                    schema_version="2.0",
                    timestamp_ms=frame.timestamp_ms,
                    source=self.extractor_id,
                    frame_ref=str(frame_path),
                    shot_id=frame.shot_id,
                    label=det["label"],
                    bbox=det["bbox"],
                    confidence=det["confidence"],
                    model_name=model_id,
                    model_version=model_version,
                )

    @property
    def extractor_id(self) -> str:
        if self.runtime is not None:
            return f"object.runtime.{self.runtime.runtime_id}"
        return "object.unknown.v1"
