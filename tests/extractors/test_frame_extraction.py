from pathlib import Path

from vindex.core.schemas.observations import FrameObservation, ShotObservation
from vindex.extractors.frame_extraction.pyav_extractor import PyAVFrameExtractor


def test_frame_extractor_middle_strategy(tmp_path):
    extractor = PyAVFrameExtractor(sampling_strategy="middle")
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    # We mock 1 shot spanning the entire 5s video
    shot = ShotObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="test",
        shot_id="sh001",
        start_ms=0,
        end_ms=5000,
    )
    
    config = {
        "shots": [shot],
        "output_dir": str(tmp_path),
        "use_cache": False,  # Bypass cache for direct extractor test
    }
    
    observations = list(extractor.extract(video_path, config))
    
    assert len(observations) == 1
    frame_obs = observations[0]
    assert isinstance(frame_obs, FrameObservation)
    assert frame_obs.shot_id == "sh001"
    # Target time in the middle of 0-5000 is 2500ms
    assert frame_obs.timestamp_ms == 2500
    
    # Verify file is saved on disk
    saved_path = Path(frame_obs.frame_path)
    assert saved_path.exists()
    assert saved_path.suffix == ".png"
    assert frame_obs.frame_hash != ""


def test_frame_extractor_first_last_strategy(tmp_path):
    extractor = PyAVFrameExtractor(sampling_strategy="first_last")
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    shot = ShotObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="test",
        shot_id="sh001",
        start_ms=0,
        end_ms=5000,
    )
    
    config = {
        "shots": [shot],
        "output_dir": str(tmp_path),
        "use_cache": False,
    }
    
    observations = list(extractor.extract(video_path, config))
    
    assert len(observations) == 2
    assert observations[0].timestamp_ms == 0
    assert observations[1].timestamp_ms == 5000
    
    assert Path(observations[0].frame_path).exists()
    assert Path(observations[1].frame_path).exists()


def test_frame_extractor_uniform_n_strategy(tmp_path):
    extractor = PyAVFrameExtractor(sampling_strategy="uniform_n", uniform_n=3)
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    shot = ShotObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="test",
        shot_id="sh001",
        start_ms=0,
        end_ms=5000,
    )
    
    config = {
        "shots": [shot],
        "output_dir": str(tmp_path),
        "use_cache": False,
    }
    
    observations = list(extractor.extract(video_path, config))
    
    assert len(observations) == 3
    # Uniform timestamps: 0, 2500, 5000
    assert observations[0].timestamp_ms == 0
    assert observations[1].timestamp_ms == 2500
    assert observations[2].timestamp_ms == 5000
