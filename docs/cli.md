# Command Line Interface (CLI) and SDK

The `vindex` CLI and Python SDK provide the primary interface for compiling videos into Visual Memory Indexes.

## CLI Usage

Run `vindex compile` on any video path:

```bash
vindex compile path/to/video.mp4 --output-dir ./compiled_index
```

### Options

- `-o, --output-dir PATH` — Directory to save outputs (defaults to `./dist`).
- `-t, --transcript-path PATH` — Pre-existing Whisper transcript JSON file (bypass audio ASR models).
- `--use-cache / --no-use-cache` — Toggle extractor observation cache.
- `--cache-dir PATH` — Directory for cached observations.
- `--asr-model-dir PATH` — Local folder with FasterWhisper model weights.
- `--det-model-dir PATH` — Local folder with PaddleOCR detection model.
- `--rec-model-dir PATH` — Local folder with PaddleOCR recognition model.
- `--vlm-model-dir PATH` — Local folder with MLX Qwen2.5-VL weights.
- `--embed-model-dir PATH` — Local folder with MiniLM embedding weights.
- `--similarity-threshold FLOAT` — Grouping cosine threshold (default `0.65`).
- `--max-gap-ms INTEGER` — Maximum allowed time gap within a scene (default `5000` ms).
- `--sampling-strategy TEXT` — Sampling strategy (`middle`, `first_last`, `uniform_n`).
- `--uniform-n INTEGER` — Number of frames to sample if using `uniform_n`.

---

## Python SDK

You can programmatically compile videos in Python:

```python
from pathlib import Path
from vindex import compile_video

config = {
    "transcript_path": "transcript.json",
    "use_cache": True,
}

visual_memory = compile_video(
    video_path=Path("video.mp4"),
    output_dir=Path("./compiled"),
    config=config
)

print(f"Compiled memory hash: {visual_memory.video_hash}")
```
