import hashlib
import io
import os
from pathlib import Path
from typing import Any, Iterator, cast

import av

from vindex.core.interfaces.extractor import Extractor
from vindex.core.schemas.observations import FrameObservation, ShotObservation


class PyAVFrameExtractor(Extractor):
    """Keyframe extraction using PyAV."""

    def __init__(self, sampling_strategy: str = "middle", uniform_n: int = 3) -> None:
        self.sampling_strategy = sampling_strategy
        self.uniform_n = uniform_n

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[FrameObservation]:
        """Sample keyframes from the video for the given shots."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Get shots from config
        shots = config.get("shots")
        if not shots:
            raise ValueError("FrameExtractor requires a list of 'shots' in the configuration dict.")

        # Ensure shot observations are correctly typed
        shot_list: list[ShotObservation] = []
        for shot in shots:
            if isinstance(shot, dict):
                shot_list.append(ShotObservation.model_validate(shot))
            elif isinstance(shot, ShotObservation):
                shot_list.append(shot)
            else:
                raise TypeError(f"Invalid shot type in config: {type(shot)}")

        # Parse sampling config
        strategy = config.get("sampling_strategy", self.sampling_strategy)
        uniform_n = config.get("uniform_n", self.uniform_n)

        # Generate target timestamps chronologically
        targets = []
        for shot in shot_list:
            start = shot.start_ms
            end = shot.end_ms
            shot_id = shot.shot_id

            if strategy == "middle":
                shot_targets = [(start + end) // 2]
            elif strategy == "first_last":
                shot_targets = [start, end]
            elif strategy == "uniform_n":
                if uniform_n > 1:
                    shot_targets = [
                        start + i * (end - start) // (uniform_n - 1)
                        for i in range(uniform_n)
                    ]
                else:
                    shot_targets = [(start + end) // 2]
            else:
                raise ValueError(f"Unknown sampling strategy: {strategy}")

            for t in shot_targets:
                targets.append({"target_ms": t, "shot_id": shot_id})

        # Sort targets chronologically
        # Sort targets chronologically
        targets = sorted(targets, key=lambda x: cast(int, x["target_ms"]))

        # Setup output directory
        output_dir_str = config.get("output_dir")
        if output_dir_str:
            output_dir = Path(output_dir_str) / "frames"
        else:
            output_dir = Path(os.path.expanduser("~/.vindex/frames"))
        os.makedirs(output_dir, exist_ok=True)

        # Open video container
        container = av.open(str(video_path))
        
        # We need to process sequentially and find the frame closest to each target
        target_idx = 0
        best_candidate = None
        best_dist = float("inf")
        finalized: list[tuple[dict[str, Any], Any]] = []

        try:
            for frame in container.decode(video=0):
                frame_ms = int(frame.time * 1000)

                while target_idx < len(targets):
                    target = targets[target_idx]
                    target_ms = cast(int, target["target_ms"])
                    dist = abs(frame_ms - target_ms)

                    if dist < best_dist:
                        best_dist = dist
                        # Convert to PIL Image immediately to avoid container frame release issues
                        best_candidate = frame.to_image()  # type: ignore[no-untyped-call]
                        break
                    else:
                        # Distance is increasing; the previous candidate was the closest
                        if best_candidate is not None:
                            finalized.append((target, best_candidate))
                        target_idx += 1
                        best_dist = float("inf")
                        best_candidate = None
                        # Re-evaluate current frame for next target

            # Finalize any remaining targets at the end of the video
            while target_idx < len(targets):
                target = targets[target_idx]
                if best_candidate is not None:
                    finalized.append((target, best_candidate))
                target_idx += 1
                best_dist = float("inf")
                best_candidate = None

        finally:
            container.close()

        # Save finalized frames and yield observations
        for target, img in finalized:
            target_ms = cast(int, target["target_ms"])
            shot_id = cast(str, target["shot_id"])

            # Save to PNG
            filename = f"{shot_id}_{target_ms}.png"
            filepath = output_dir / filename
            img.save(filepath, format="PNG")

            # Compute SHA-256 hash of image bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_bytes = img_byte_arr.getvalue()
            frame_hash = hashlib.sha256(img_bytes).hexdigest()

            yield FrameObservation(
                schema_version="1.0",
                timestamp_ms=target_ms,
                source=self.extractor_id,
                shot_id=shot_id,
                frame_path=str(filepath),
                frame_hash=frame_hash,
            )

    @property
    def extractor_id(self) -> str:
        return "frame_extraction.pyav.v1"
