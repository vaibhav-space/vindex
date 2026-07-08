# OCR Extractor

The OCR (Optical Character Recognition) extractor extracts text regions from sampled video keyframes. It is backend-agnostic and relies on dependency-injected runtimes.

## Class Details

- **Implementation:** `OCRExtractor`
- **Path:** `vindex/extractors/ocr/ocr_extractor.py`
- **ID:** `ocr.runtime.<runtime_id>`

## Inputs and Configuration

The `extract` method accepts:
1. `video_path: Path` — Local path to the video file.
2. `config: dict[str, Any]` — Configuration dictionary containing:
   - `frames: list[FrameObservation]` (required) — The list of sampled keyframes to run OCR on.

## Injected Runtimes

### `PaddleOCRRuntime`

- **Backend:** `paddleocr` (utilizing PaddlePaddle)
- **ID:** `paddleocr.v1`
- **Configuration:**
  - `det_model_dir: str` (required) — Local directory path containing detection model weights.
  - `rec_model_dir: str` (required) — Local directory path containing recognition model weights.
  - `cls_model_dir: str` (optional) — Local directory path containing classification model weights.
  - `use_gpu: bool` (default `False`) — Set to `True` to enable GPU acceleration if supported.
  - `lang: str` (default `"en"`) — Detection language support.

## Emitted Observations

Emits a stream of `OCRObservation` objects:

```json
{
  "schema_version": "1.0",
  "timestamp_ms": 1000,
  "source": "ocr.runtime.paddleocr.v1",
  "text": "Slide Title",
  "bbox": [10.0, 20.0, 100.0, 30.0],
  "frame_ref": "/Users/user/.vindex/frames/sh001_1000.png",
  "confidence": 0.98
}
```

## Known Limitations

- **Model path constraint:** You must download the model files and provide `det_model_dir` and `rec_model_dir` in config explicitly. Automatic downloads are disabled by default for privacy and local-first execution.
