from pathlib import Path
from typing import Any, Iterator

from scenedetect import ContentDetector, SceneManager, open_video

from vindex.core.interfaces.extractor import Extractor
from vindex.core.schemas.observations import ShotObservation


class PySceneDetectExtractor(Extractor):
    """Shot detection extractor using PySceneDetect."""

    def __init__(self, threshold: float = 27.0) -> None:
        self.threshold = threshold

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[ShotObservation]:
        """Detect shots in the video using content-aware cut detection."""
        threshold = config.get("threshold", self.threshold)
        
        # PySceneDetect expects video path as string
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        video = open_video(str(video_path))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        scene_manager.detect_scenes(video=video)
        scene_list = scene_manager.get_scene_list()
        
        if not scene_list:
            # Entire video is a single shot
            start_ms = 0
            assert video.duration is not None
            end_ms = int(video.duration.seconds * 1000)
            yield ShotObservation(
                schema_version="1.0",
                timestamp_ms=start_ms,
                source=self.extractor_id,
                shot_id="sh001",
                start_ms=start_ms,
                end_ms=end_ms,
            )
        else:
            for idx, (start_tc, end_tc) in enumerate(scene_list, start=1):
                shot_id = f"sh{idx:03d}"
                start_ms = int(start_tc.seconds * 1000)
                end_ms = int(end_tc.seconds * 1000)
                
                yield ShotObservation(
                    schema_version="1.0",
                    timestamp_ms=start_ms,
                    source=self.extractor_id,
                    shot_id=shot_id,
                    start_ms=start_ms,
                    end_ms=end_ms,
                )

    @property
    def extractor_id(self) -> str:
        return "scene_detection.pyscenedetect.v1"
