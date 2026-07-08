from pathlib import Path

import pytest

from vindex.core.schemas.observations import ShotObservation
from vindex.extractors.scene_detection.pyscenedetect import PySceneDetectExtractor


def test_scene_detector_synthetic_fixture():
    extractor = PySceneDetectExtractor()
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    assert video_path.exists()
    
    observations = list(extractor.extract(video_path, {}))
    
    assert len(observations) == 1
    shot = observations[0]
    assert isinstance(shot, ShotObservation)
    assert shot.shot_id == "sh001"
    assert shot.start_ms == 0
    assert shot.end_ms == 5000
    assert shot.timestamp_ms == 0
    assert shot.source == "scene_detection.pyscenedetect.v1"


def test_scene_detector_determinism():
    extractor = PySceneDetectExtractor()
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    obs1 = list(extractor.extract(video_path, {}))
    obs2 = list(extractor.extract(video_path, {}))
    
    assert obs1 == obs2


def test_scene_detector_missing_file():
    extractor = PySceneDetectExtractor()
    with pytest.raises(Exception):
        list(extractor.extract(Path("non_existent_video.mp4"), {}))
