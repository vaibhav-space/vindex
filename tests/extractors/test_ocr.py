from pathlib import Path

import pytest

from vindex.core.interfaces.runtimes import OCRRuntime
from vindex.core.schemas.observations import FrameObservation, OCRObservation
from vindex.extractors.ocr.ocr_extractor import OCRExtractor
from vindex.runtimes.ocr.paddleocr_runtime import PaddleOCRRuntime


class MockOCRRuntime(OCRRuntime):
    """Mock OCR runtime for testing without model weights."""

    def load(self, model_dir_or_path: Path) -> None:
        pass

    def unload(self) -> None:
        pass

    def extract_text(self, frame_path: Path, config: dict) -> list[dict]:
        return [
            {"text": "Sample Text", "bbox": [10.0, 20.0, 100.0, 30.0], "confidence": 0.98}
        ]

    @property
    def runtime_id(self) -> str:
        return "mock_ocr"



def test_ocr_mock_extractor(tmp_path):
    runtime = MockOCRRuntime()
    extractor = OCRExtractor(runtime=runtime)
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    # We mock 1 frame observation
    frame_path = tmp_path / "frame.png"
    # Create empty dummy file so exists() check passes
    frame_path.touch()
    
    frame = FrameObservation(
        schema_version="1.0",
        timestamp_ms=1000,
        source="test",
        shot_id="sh001",
        frame_path=str(frame_path),
        frame_hash="mock_hash",
    )
    
    config = {
        "frames": [frame],
        "use_cache": False,
    }
    
    observations = list(extractor.extract(video_path, config))
    
    assert len(observations) == 1
    ocr_obs = observations[0]
    assert isinstance(ocr_obs, OCRObservation)
    assert ocr_obs.text == "Sample Text"
    assert ocr_obs.bbox == [10.0, 20.0, 100.0, 30.0]
    assert ocr_obs.timestamp_ms == 1000
    assert ocr_obs.frame_ref == str(frame_path)
    assert extractor.extractor_id == "ocr.runtime.mock_ocr"


def test_paddleocr_no_model_dirs_raises():
    runtime = PaddleOCRRuntime()
    with pytest.raises(ValueError, match="PaddleOCRRuntime requires 'det_model_dir'"):
        runtime.extract_text(Path("frame.png"), {})


def test_paddleocr_missing_model_dirs_raises():
    runtime = PaddleOCRRuntime()
    config = {
        "det_model_dir": "/non_existent_det",
        "rec_model_dir": "/non_existent_rec",
    }
    with pytest.raises(FileNotFoundError, match="PaddleOCR model directories not found"):
        runtime.extract_text(Path("frame.png"), config)
