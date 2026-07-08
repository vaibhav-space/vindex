# VLM Captioning Extractor

The VLM Captioning extractor generates natural language descriptions of shots based on their sampled keyframe(s) using a Vision-Language Model. It is backend-agnostic and relies on dependency-injected runtimes.

## Class Details

- **Implementation:** `VLMCaptioner`
- **Path:** `vindex/extractors/vlm_caption/vlm_captioner.py`
- **ID:** `vlm_caption.runtime.<runtime_id>`

## Inputs and Configuration

The `extract` method accepts:
1. `video_path: Path` — Local path to the video file.
2. `config: dict[str, Any]` — Configuration dictionary containing:
   - `shots: list[ShotObservation]` (required) — List of detected shots.
   - `frames: list[FrameObservation]` (required) — List of sampled keyframes corresponding to the shots.
   - `prompt: str` (optional) — Vision-Language model prompt (defaults to a concise factual description prompt).

## Injected Runtimes

### `MLXVLMRuntime`

- **Backend:** `mlx-vlm` (Metal-accelerated on Apple Silicon)
- **ID:** `mlx_vlm.v1`
- **Configuration:**
  - `model_dir: str` (required) — Local directory path containing downloaded VLM model weights (no auto-downloads allowed).
  - `max_tokens: int` (default `128`) — Maximum number of generated tokens for the caption.
  - `temperature: float` (default `0.0`) — Sampling temperature.

## Emitted Observations

Emits a stream of `CaptionObservation` objects:

```json
{
  "schema_version": "1.0",
  "timestamp_ms": 0,
  "source": "vlm_caption.runtime.mlx_vlm.v1",
  "shot_id": "sh001",
  "caption_text": "A close up of a person speaking in front of a blue background.",
  "model_id": "qwen2.5-vl-7b-instruct",
  "model_version": "1.0"
}
```

## Known Limitations

- **Apple Silicon Native:** `MLXVLMRuntime` relies on `mlx-vlm` and is only supported on Apple Silicon Macs. For other environments, a fallback runtime must be implemented.
- **Model weights required:** Model weights must be downloaded and stored locally. Auto-downloads are disabled to enforce local-first privacy.
