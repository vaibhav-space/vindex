import json
from pathlib import Path

import pytest

from vindex.core.interfaces.runtimes import ASRRuntime
from vindex.core.schemas.observations import ASRWordObservation
from vindex.extractors.asr.asr_extractor import ASRExtractor
from vindex.runtimes.asr.faster_whisper_runtime import FasterWhisperRuntime
from vindex.runtimes.asr.whisper_cpp_runtime import WhisperCppRuntime


class MockASRRuntime(ASRRuntime):
    """Mock ASR runtime for CI test isolation."""

    def load(self, model_dir_or_path: Path) -> None:
        pass

    def unload(self) -> None:
        pass

    def transcribe(self, audio_path: Path, config: dict) -> list[dict]:
        return [
            {"word": "hello", "start": 0.5, "end": 1.0, "confidence": 0.95},
            {"word": "world", "start": 1.1, "end": 1.8, "confidence": 0.99},
        ]

    @property
    def runtime_id(self) -> str:
        return "mock_asr"



def test_asr_passthrough_mode(tmp_path):
    # Setup a mock transcript file
    transcript_data = {
        "words": [
            {"word": "mock", "start": 0.0, "end": 0.5, "confidence": 0.9},
            {"word": "test", "start": 0.6, "end": 1.2, "confidence": 0.95},
        ]
    }
    transcript_file = tmp_path / "transcript.json"
    with open(transcript_file, "w") as f:
        json.dump(transcript_data, f)

    extractor = ASRExtractor()
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    config = {
        "transcript_path": str(transcript_file),
        "use_cache": False,
    }
    
    observations = list(extractor.extract(video_path, config))
    
    assert len(observations) == 2
    assert isinstance(observations[0], ASRWordObservation)
    assert observations[0].word == "mock"
    assert observations[0].start_ms == 0
    assert observations[0].end_ms == 500
    
    assert observations[1].word == "test"
    assert observations[1].start_ms == 600
    assert observations[1].end_ms == 1200


def test_asr_mock_runtime_mode():
    runtime = MockASRRuntime()
    extractor = ASRExtractor(runtime=runtime)
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    config = {
        "use_cache": False,
    }
    
    observations = list(extractor.extract(video_path, config))
    
    assert len(observations) == 2
    assert observations[0].word == "hello"
    assert observations[0].start_ms == 500
    assert observations[0].end_ms == 1000
    
    assert observations[1].word == "world"
    assert observations[1].start_ms == 1100
    assert observations[1].end_ms == 1800
    assert extractor.extractor_id == "asr.runtime.mock_asr"


def test_faster_whisper_no_model_dir_raises():
    runtime = FasterWhisperRuntime()
    with pytest.raises(ValueError, match="FasterWhisperRuntime requires 'model_dir'"):
        runtime.transcribe(Path("audio.wav"), {})


def test_faster_whisper_missing_model_dir_raises():
    runtime = FasterWhisperRuntime()
    with pytest.raises(FileNotFoundError, match="CTranslate2 model weights not found"):
        runtime.transcribe(Path("audio.wav"), {"model_dir": "/non_existent_path"})


def test_whisper_cpp_no_binary_path_raises():
    runtime = WhisperCppRuntime()
    with pytest.raises(ValueError, match="WhisperCppRuntime requires 'binary_path'"):
        runtime.transcribe(Path("audio.wav"), {})


def test_whisper_cpp_missing_binary_raises():
    runtime = WhisperCppRuntime()
    with pytest.raises(FileNotFoundError, match="whisper.cpp binary not found"):
        runtime.transcribe(Path("audio.wav"), {"binary_path": "/non_existent_binary"})
