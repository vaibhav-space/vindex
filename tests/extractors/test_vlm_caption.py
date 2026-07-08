from pathlib import Path

import pytest

from vindex.core.interfaces.runtimes import SceneUnderstandingRuntime
from vindex.core.schemas.observations import (
    CaptionObservation,
    FrameObservation,
    ShotObservation,
)
from vindex.extractors.vlm_caption.vlm_captioner import VLMCaptioner
from vindex.runtimes.vision.mlx_vlm_runtime import MLXVLMRuntime


class MockVisionRuntime(SceneUnderstandingRuntime):
    """Mock VLM runtime for CI isolation."""

    def load(self, model_dir_or_path: Path) -> None:
        pass

    def unload(self) -> None:
        pass

    def describe_scene(self, frame_paths: list[Path], prompt: str, config: dict) -> str:
        return "A mock description of the frame."

    @property
    def runtime_id(self) -> str:
        return "mock_vision"



def test_vlm_captioner_mock():
    runtime = MockVisionRuntime()
    extractor = VLMCaptioner(runtime=runtime)
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    # We mock 1 shot and 1 frame
    shot = ShotObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="test",
        shot_id="sh001",
        start_ms=0,
        end_ms=5000,
    )
    
    frame = FrameObservation(
        schema_version="1.0",
        timestamp_ms=2500,
        source="test",
        shot_id="sh001",
        frame_path="eval/golden/fixture_001/frames/sh001_2500.png",
        frame_hash="mock_hash",
    )
    
    config = {
        "shots": [shot],
        "frames": [frame],
        "use_cache": False,
    }
    
    observations = list(extractor.extract(video_path, config))
    
    assert len(observations) == 1
    caption_obs = observations[0]
    assert isinstance(caption_obs, CaptionObservation)
    assert caption_obs.shot_id == "sh001"
    assert caption_obs.caption_text == "A mock description of the frame."
    assert extractor.extractor_id == "vlm_caption.runtime.mock_vision"


def test_mlx_vlm_runtime_no_model_dir_raises():
    runtime = MLXVLMRuntime()
    with pytest.raises(ValueError, match="MLXVLMRuntime requires 'model_dir'"):
        runtime.describe_scene([Path("frame.png")], "prompt", {})


def test_mlx_vlm_runtime_missing_model_dir_raises():
    runtime = MLXVLMRuntime()
    with pytest.raises(FileNotFoundError, match="MLX VLM model directory not found"):
        runtime.describe_scene([Path("frame.png")], "prompt", {"model_dir": "/non_existent_model"})


def test_vlm_captioner_masking(tmp_path):
    # Mock runtime to capture the arguments passed to describe_scene
    class CaptureVisionRuntime(MockVisionRuntime):
        def __init__(self):
            self.captured_frame_paths = None
            self.captured_prompt = None

        def describe_scene(self, frame_paths: list[Path], prompt: str, config: dict) -> str:
            self.captured_frame_paths = frame_paths
            self.captured_prompt = prompt
            return "Masked background description."

    runtime = CaptureVisionRuntime()
    extractor = VLMCaptioner(runtime=runtime)
    
    # Create a real dummy image so PIL can load it and draw on it
    from PIL import Image
    dummy_img_path = tmp_path / "shot_frame.png"
    img = Image.new("RGB", (100, 100), color="white")
    img.save(dummy_img_path)

    shot = ShotObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="test",
        shot_id="sh001",
        start_ms=0,
        end_ms=5000,
    )
    
    frame = FrameObservation(
        schema_version="1.0",
        timestamp_ms=2500,
        source="test",
        shot_id="sh001",
        frame_path=str(dummy_img_path),
        frame_hash="mock_hash",
    )
    
    ocr_obs = {
        "frame_ref": str(dummy_img_path),
        "bbox": [10.0, 10.0, 30.0, 20.0],  # bounding box to mask
        "text": "Ignore me",
        "confidence": 0.99,
    }

    config = {
        "shots": [shot],
        "frames": [frame],
        "ocr_obs": [ocr_obs],
        "scene_understanding.ignore_text_regions": True,
        "use_cache": False,
    }
    
    observations = list(extractor.extract(Path("video.mp4"), config))
    
    assert len(observations) == 1
    assert observations[0].caption_text == "Masked background description."
    
    # Verify coordinates masking occurred
    assert runtime.captured_frame_paths is not None
    assert len(runtime.captured_frame_paths) == 1
    
    masked_path = runtime.captured_frame_paths[0]
    # The path passed should be the temporary masked file, not the original dummy_img_path
    assert masked_path.resolve() != dummy_img_path.resolve()
    # The temporary masked file should have been cleaned up/deleted
    assert not masked_path.exists()
    
    # Verify prompt override
    assert "Describe the scene in detail" in runtime.captured_prompt





