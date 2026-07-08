from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterator

from vindex.core.cache import ObservationCache, get_cache_key, get_video_hash
from vindex.core.schemas.observations import BaseObservation


class Extractor(ABC):
    """Base interface for all vindex extraction stages.

    All extractors participate in the caching layer automatically at the
    interface level unless disabled in the configuration.
    """

    def extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[BaseObservation]:
        """Orchestrate extraction with content-addressed caching."""
        # Check if caching is explicitly disabled
        use_cache = config.get("use_cache", True)
        
        if not use_cache:
            yield from self._extract(video_path, config)
            return

        # Initialize cache
        cache_dir = config.get("cache_dir")
        cache = ObservationCache(cache_dir=Path(cache_dir) if cache_dir else None)

        try:
            # Generate cache key
            video_hash = get_video_hash(video_path)
            # Remove objects like 'shots' from the config hash to keep it serializable/clean
            clean_config = {k: v for k, v in config.items() if k not in ("shots", "cache_dir", "output_dir")}
            cache_key = get_cache_key(video_hash, self.extractor_id, clean_config)

            # Check cache
            cached_observations = cache.get(cache_key)
            if cached_observations is not None:
                # Cache hit
                yield from cached_observations
                return

            # Cache miss - compute observations
            observations = list(self._extract(video_path, config))
            
            # Store in cache
            cache.put(cache_key, observations)
            
            # Yield observations
            yield from observations

        finally:
            cache.close()

    @abstractmethod
    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[BaseObservation]:
        """Subclass implementation of the extraction logic."""
        ...

    @property
    @abstractmethod
    def extractor_id(self) -> str:
        """Stable identifier for the extractor (e.g. 'scene_detection.pyscenedetect.v1')."""
        ...
