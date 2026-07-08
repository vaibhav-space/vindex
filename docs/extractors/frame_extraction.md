# Frame Extraction Extractor

The Frame Extraction extractor decodes video frames using PyAV and samples specific keyframes for each detected shot based on the configured sampling strategy.

## Class Details

- **Implementation:** `PyAVFrameExtractor`
- **Path:** `vindex/extractors/frame_extraction/pyav_extractor.py`
- **Default Backend:** PyAV (`av` Python package)
- **ID:** `frame_extraction.pyav.v1`

## Inputs and Configuration

The `extract` method accepts:
1. `video_path: Path` — The local path to the video file.
2. `config: dict[str, Any]` — Configuration dictionary containing:
   - `shots: list[ShotObservation]` (required) — The list of shot boundaries to extract frames from.
   - `sampling_strategy: str` (default `"middle"`) — The strategy for choosing frame timestamps:
     - `"middle"`: Samples the single frame at the exact midpoint of the shot.
     - `"first_last"`: Samples two frames, one at the start and one at the end of the shot.
     - `"uniform_n"`: Samples `n` frames evenly spaced across the shot duration.
   - `uniform_n: int` (default `3`) — Number of frames to sample if `sampling_strategy` is `"uniform_n"`.
   - `output_dir: str` — Directory to save keyframe PNGs (defaults to `~/.vindex/frames/`).

## Emitted Observations

Emits a stream of `FrameObservation` objects:

```json
{
  "schema_version": "1.0",
  "timestamp_ms": 2500,
  "source": "frame_extraction.pyav.v1",
  "shot_id": "sh001",
  "frame_path": "/Users/user/.vindex/frames/sh001_2500.png",
  "frame_hash": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
}
```

## Known Limitations

- **Sequential Scan:** For long videos, a sequential scan of frames is used. While robust and accurate, it may take longer for multi-hour videos compared to keyframe-only seeking.
