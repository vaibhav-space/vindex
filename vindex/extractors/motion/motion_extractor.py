from pathlib import Path
from typing import Any, Iterator, Optional

from vindex.core.interfaces.extractor import Extractor
from vindex.core.interfaces.runtimes import MotionAnalysisRuntime
from vindex.core.schemas.observations import (
    FrameObservation,
    MotionObservation,
    ShotObservation,
)


class MotionExtractor(Extractor):
    """Motion analysis extractor using a registered MotionAnalysisRuntime."""

    def __init__(self, runtime: Optional[MotionAnalysisRuntime] = None) -> None:
        self.runtime = runtime

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[MotionObservation]:
        """Analyze camera movement and optical flow magnitude."""
        if self.runtime is None:
            raise ValueError("MotionExtractor requires a MotionAnalysisRuntime injected during initialization.")

        shots = config.get("shots")
        frames = config.get("frames")
        if not shots or not frames:
            raise ValueError("MotionExtractor requires both 'shots' and 'frames' in configuration.")

        # Parse shots
        shot_list: list[ShotObservation] = []
        for s in shots:
            if isinstance(s, dict):
                shot_list.append(ShotObservation.model_validate(s))
            elif isinstance(s, ShotObservation):
                shot_list.append(s)
            else:
                raise TypeError(f"Invalid shot type in config: {type(s)}")

        # Parse frames
        frame_list: list[FrameObservation] = []
        for f in frames:
            if isinstance(f, dict):
                frame_list.append(FrameObservation.model_validate(f))
            elif isinstance(f, FrameObservation):
                frame_list.append(f)
            else:
                raise TypeError(f"Invalid frame type in config: {type(f)}")

        for shot in shot_list:
            shot_id = shot.shot_id
            # Sort shot frames by timestamp
            shot_frames = sorted(
                [f for f in frame_list if f.shot_id == shot_id],
                key=lambda f: f.timestamp_ms
            )

            if len(shot_frames) < 2:
                # Need at least two frames to calculate motion
                continue

            frame_paths = [Path(f.frame_path) for f in shot_frames]

            # Run motion runtime
            res = self.runtime.analyze_motion(frame_paths, config)

            yield MotionObservation(
                schema_version="2.0",
                timestamp_ms=shot.start_ms,
                duration_ms=shot.end_ms - shot.start_ms,
                source=self.extractor_id,
                shot_id=shot_id,
                motion_score=res["motion_score"],
                camera_movement=res["camera_movement"],
            )

    @property
    def extractor_id(self) -> str:
        if self.runtime is not None:
            return f"motion.runtime.{self.runtime.runtime_id}"
        return "motion.unknown.v1"
