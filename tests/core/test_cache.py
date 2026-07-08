from pathlib import Path
from typing import Any, Iterator

from vindex.core.cache import ObservationCache, get_cache_key
from vindex.core.interfaces.extractor import Extractor
from vindex.core.schemas.observations import BaseObservation, ShotObservation


class DummyExtractor(Extractor):
    """A mock extractor that counts how many times _extract was called."""

    def __init__(self) -> None:
        self.call_count = 0

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[BaseObservation]:
        self.call_count += 1
        yield ShotObservation(
            schema_version="1.0",
            timestamp_ms=0,
            source=self.extractor_id,
            shot_id="sh001",
            start_ms=0,
            end_ms=1000,
        )

    @property
    def extractor_id(self) -> str:
        return "scene_detection.dummy.v1"


def test_cache_key_generation():
    video_hash = "mock_hash"
    extractor_id = "test_extractor"
    config1 = {"param": "value", "shots": [1, 2]}
    config2 = {"param": "value", "cache_dir": "/tmp"}
    
    # 'shots' and 'cache_dir' are removed from key config in Extractor.extract,
    # but let's test get_cache_key with raw configs
    key1 = get_cache_key(video_hash, extractor_id, config1)
    key2 = get_cache_key(video_hash, extractor_id, config1)
    assert key1 == key2


def test_observation_cache_put_get(tmp_path):
    cache = ObservationCache(cache_dir=tmp_path)
    
    obs = [
        ShotObservation(
            schema_version="1.0",
            timestamp_ms=100,
            source="test",
            shot_id="sh001",
            start_ms=0,
            end_ms=200,
        )
    ]
    
    cache_key = "test_key"
    assert cache.get(cache_key) is None
    
    cache.put(cache_key, obs)
    
    cached_obs = cache.get(cache_key)
    assert cached_obs is not None
    assert len(cached_obs) == 1
    assert cached_obs[0].shot_id == "sh001"
    assert cached_obs[0].timestamp_ms == 100
    
    cache.close()


def test_extractor_cache_integration(tmp_path):
    extractor = DummyExtractor()
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    config = {
        "cache_dir": str(tmp_path),
        "use_cache": True,
    }
    
    # First call: cache miss, calls _extract
    obs1 = list(extractor.extract(video_path, config))
    assert extractor.call_count == 1
    assert len(obs1) == 1
    
    # Second call: cache hit, does NOT call _extract
    obs2 = list(extractor.extract(video_path, config))
    assert extractor.call_count == 1  # call_count remains 1
    assert obs1 == obs2


def test_extractor_cache_disabled(tmp_path):
    extractor = DummyExtractor()
    video_path = Path("eval/golden/fixture_001/video.mp4")
    
    config = {
        "cache_dir": str(tmp_path),
        "use_cache": False,
    }
    
    # First call
    obs1 = list(extractor.extract(video_path, config))
    assert extractor.call_count == 1
    
    # Second call with use_cache=False: calls _extract again
    obs2 = list(extractor.extract(video_path, config))
    assert extractor.call_count == 2
