# ruff: noqa: E402
import sys
from unittest.mock import MagicMock, patch

mock_ultralytics = MagicMock()
sys.modules["ultralytics"] = mock_ultralytics

from pathlib import Path

import pytest
from PIL import Image

from vindex.core.schemas.observations import (
    FrameObservation,
    MotionObservation,
    ObjectObservation,
    ShotObservation,
)
from vindex.extractors.motion.motion_extractor import MotionExtractor
from vindex.extractors.objects.object_extractor import ObjectExtractor
from vindex.runtimes.motion.opencv_runtime import OpenCVFlowRuntime
from vindex.runtimes.objects.yolov8_runtime import YOLOv8ObjectDetectionRuntime


@patch("ultralytics.YOLO")
def test_yolov8_object_extractor(mock_yolo_cls, tmp_path):

    # Setup mock YOLO instance
    mock_yolo = MagicMock()
    mock_box1 = MagicMock()
    mock_box1.cls = [0]
    mock_box1.xyxy = [[10.0, 20.0, 50.0, 60.0]]
    mock_box1.conf = [0.95]
    
    mock_result = MagicMock()
    mock_result.boxes = [mock_box1]
    mock_result.names = {0: "person"}
    
    mock_yolo.return_value = [mock_result]
    mock_yolo_cls.return_value = mock_yolo

    runtime = YOLOv8ObjectDetectionRuntime()
    extractor = ObjectExtractor(runtime=runtime)

    # Create dummy frame file
    frame_file = tmp_path / "frame_001.png"
    Image.new("RGB", (100, 100), color="white").save(frame_file)

    # Create dummy model file
    model_file = tmp_path / "yolo.pt"
    model_file.touch()

    frame = FrameObservation(
        schema_version="1.0",
        timestamp_ms=1000,
        source="test",
        shot_id="sh001",
        frame_path=str(frame_file),
        frame_hash="mock_hash",
    )

    config = {
        "frames": [frame],
        "object_model_dir": str(model_file),
        "model_dir": str(model_file),
        "use_cache": False,
    }


    obs = list(extractor.extract(Path("video.mp4"), config))
    assert len(obs) == 1
    
    obj_obs = obs[0]
    assert isinstance(obj_obs, ObjectObservation)
    assert obj_obs.label == "person"
    assert obj_obs.bbox == [10.0, 20.0, 40.0, 40.0]
    assert obj_obs.confidence == pytest.approx(0.95)
    assert obj_obs.shot_id == "sh001"


def test_opencv_motion_extractor(tmp_path):
    runtime = OpenCVFlowRuntime()
    extractor = MotionExtractor(runtime=runtime)

    # Create two slightly different frame images to simulate motion
    frame_file1 = tmp_path / "frame_001.png"
    frame_file2 = tmp_path / "frame_002.png"
    
    Image.new("RGB", (100, 100), color="white").save(frame_file1)
    
    # Second frame has a black square drawn on it
    img2 = Image.new("RGB", (100, 100), color="white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img2)
    draw.rectangle([30, 30, 70, 70], fill="black")
    img2.save(frame_file2)

    shot = ShotObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="test",
        shot_id="sh001",
        start_ms=0,
        end_ms=2000,
    )

    frame1 = FrameObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="test",
        shot_id="sh001",
        frame_path=str(frame_file1),
        frame_hash="hash1",
    )

    frame2 = FrameObservation(
        schema_version="1.0",
        timestamp_ms=1000,
        source="test",
        shot_id="sh001",
        frame_path=str(frame_file2),
        frame_hash="hash2",
    )

    config = {
        "shots": [shot],
        "frames": [frame1, frame2],
        "use_cache": False,
    }

    obs = list(extractor.extract(Path("video.mp4"), config))
    assert len(obs) == 1
    
    motion_obs = obs[0]
    assert isinstance(motion_obs, MotionObservation)
    # Motion score should be greater than zero due to the black square difference
    assert motion_obs.motion_score > 0.0
    assert motion_obs.camera_movement in ["static", "zoom", "pan", "tilt"]
    assert motion_obs.shot_id == "sh001"
