# ASR Extractor

The ASR (Automated Speech Recognition) extractor transcribes audio from the video into word-level observations. It is completely backend-agnostic and relies on dependency-injected runtimes.

## Class Details

- **Implementation:** `ASRExtractor`
- **Path:** `vindex/extractors/asr/asr_extractor.py`
- **ID:** `asr.passthrough.v1` (if using passthrough transcript) or `asr.runtime.<runtime_id>` (if using model runtime)

## Inputs and Configuration

The `extract` method accepts:
1. `video_path: Path` — Local path to the video file.
2. `config: dict[str, Any]` — Configuration dictionary containing:
   - `transcript_path: str` (optional) — Path to a pre-existing transcript JSON file. If provided, the extractor reads and parses this file directly, skipping audio extraction and model inference.
   - `ffmpeg_path: str` (default `"ffmpeg"`) — Path to the ffmpeg executable, used to extract audio from the video.

## Injected Runtimes

When not using a pre-existing transcript, `ASRExtractor` requires a concrete ASR runtime implementation:

### `FasterWhisperRuntime`

- **Backend:** `faster-whisper`
- **ID:** `faster_whisper.v1`
- **Configuration:**
  - `model_dir: str` (required) — Local directory path containing CTranslate2-converted model weights (no auto-downloads allowed).
  - `device: str` (default `"cpu"`) — Execution device (`"cpu"`, `"cuda"`, or `"mps"`).
  - `compute_type: str` (default `"int8"`) — Quantization level (e.g. `"int8"`, `"float16"`).

### `WhisperCppRuntime`

- **Backend:** `whisper.cpp`
- **ID:** `whisper_cpp.v1`
- **Configuration:**
  - `binary_path: str` (required) — Path to the compiled `main` (whisper.cpp) executable.
  - `model_path: str` (required) — Path to the GGUF model weights file.
  - `threads: int` (optional) — Number of CPU threads to use.

## Emitted Observations

Emits a stream of `ASRWordObservation` objects:

```json
{
  "schema_version": "1.0",
  "timestamp_ms": 500,
  "source": "asr.runtime.faster_whisper.v1",
  "word": "hello",
  "start_ms": 500,
  "end_ms": 1000,
  "confidence": 0.95
}
```

## Known Limitations

- **FFmpeg dependency:** Requires `ffmpeg` installed on the system to extract audio from the video container.
- **Conversion required:** `FasterWhisperRuntime` requires model weights to be in CTranslate2 format, not raw huggingface PyTorch weights.
