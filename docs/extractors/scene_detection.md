# Scene Detection Extractor

The Scene Detection extractor detects shot boundaries (cuts and fades) in the input video, dividing it into raw, continuous camera takes.

## Class Details

- **Implementation:** `PySceneDetectExtractor`
- **Path:** `vindex/extractors/scene_detection/pyscenedetect.py`
- **Default Backend:** PySceneDetect (`scenedetect` Python package)
- **ID:** `scene_detection.pyscenedetect.v1`

## Inputs and Configuration

The `extract` method accepts:
1. `video_path: Path` — The local path to the video file.
2. `config: dict[str, Any]` — Configuration dictionary containing:
   - `threshold: float` (default `27.0`) — Sensitivity threshold for detecting cuts. Lower values are more sensitive.

## Emitted Observations

Emits a stream of `ShotObservation` objects:

```json
{
  "schema_version": "1.0",
  "timestamp_ms": 0,
  "source": "scene_detection.pyscenedetect.v1",
  "shot_id": "sh001",
  "start_ms": 0,
  "end_ms": 5000
}
```

## Known Limitations

- **Gradual Transitions:** Cross-fades and slow dissolves might be missed if the threshold is too high.
- **Fast Motion:** Rapid camera motion or flashing lights can occasionally trigger false positive cut detections.
