import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

import diskcache
from pydantic import BaseModel

from vindex.core.schemas.observations import (
    ASRWordObservation,
    AudioEventObservation,
    CaptionObservation,
    ColorObservation,
    FrameObservation,
    LayoutObservation,
    MotionObservation,
    ObjectObservation,
    OCRObservation,
    ShotObservation,
)

# Map observation class name to type for deserialization
OBSERVATION_TYPES: dict[str, type[BaseModel]] = {
    "ShotObservation": ShotObservation,
    "FrameObservation": FrameObservation,
    "ASRWordObservation": ASRWordObservation,
    "OCRObservation": OCRObservation,
    "CaptionObservation": CaptionObservation,
    "ObjectObservation": ObjectObservation,
    "MotionObservation": MotionObservation,
    "LayoutObservation": LayoutObservation,
    "ColorObservation": ColorObservation,
    "AudioEventObservation": AudioEventObservation,
}



def get_video_hash(video_path: Path) -> str:
    """Compute the SHA-256 hash of a video file's contents."""
    sha256 = hashlib.sha256()
    with open(video_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_cache_key(video_hash: str, extractor_id: str, config: dict[str, Any]) -> str:
    """Generate a deterministic cache key from video hash, extractor ID, and config."""
    clean_cfg: dict[str, Any] = {}

    for k, v in config.items():
        if isinstance(v, (str, int, float, bool, type(None))):
            clean_cfg[k] = v
        elif isinstance(v, list):
            if all(isinstance(x, (str, int, float, bool)) for x in v):
                clean_cfg[k] = v
        elif isinstance(v, dict):
            clean_cfg[k] = {str(dk): dv for dk, dv in v.items() if isinstance(dv, (str, int, float, bool, type(None)))}
            
    config_json = json.dumps(clean_cfg, sort_keys=True)
    raw_key = f"{video_hash}:{extractor_id}:{config_json}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()



class ObservationCache:
    """Content-addressed local cache for extractor observations."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        if cache_dir is None:
            cache_dir = Path(os.path.expanduser("~/.vindex/cache"))
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = diskcache.Cache(str(cache_dir))

    def get(self, key: str) -> Optional[list[Any]]:
        """Retrieve observations from the cache. Returns None on cache miss."""
        cached_data = self.cache.get(key)
        if cached_data is None:
            return None

        # cached_data is a list of tuples (class_name, json_data)
        observations = []
        for class_name, json_data in cached_data:
            if class_name in OBSERVATION_TYPES:
                model_cls = OBSERVATION_TYPES[class_name]
                observations.append(model_cls.model_validate_json(json_data))
            else:
                raise ValueError(f"Unknown observation type: {class_name}")
        return observations

    def put(self, key: str, observations: list[Any]) -> None:
        """Store observations in the cache."""
        serialized = []
        for obs in observations:
            if not isinstance(obs, BaseModel):
                raise TypeError(f"Cached object must be a Pydantic model: {type(obs)}")
            class_name = obs.__class__.__name__
            serialized.append((class_name, obs.model_dump_json()))
        self.cache.set(key, serialized)

    def close(self) -> None:
        self.cache.close()
