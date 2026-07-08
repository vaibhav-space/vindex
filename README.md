# vindex

**The open-source video knowledge compiler.**

> Compile any video, once, into a deterministic, inspectable, versioned knowledge artifact — so no AI system ever has to watch the same video twice.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform: macOS (Apple Silicon)](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)]()
[![Status: Active Development](https://img.shields.io/badge/status-active%20development-orange.svg)]()

---

## What is vindex?

`vindex` is a local-first, open-source Python SDK and REST API that processes any video file through a modular multi-modal extraction pipeline and produces **stable, typed, versioned output artifacts** — structured JSON and human-readable Markdown — that any downstream system (AI agent, RAG pipeline, search index, video editor) can consume without ever touching the raw video again.

It is a **compiler**, not an assistant. It produces **facts**, not opinions. It runs **entirely on your machine** with no cloud account, no API key, and no data leaving your device.

Think of it as [Tesseract](https://github.com/tesseract-ocr/tesseract) — but for everything a video contains, not just the text in it.

---

## The problem it solves

Every AI system that works with video today re-derives understanding from scratch — non-reproducibly, at cost, every single time. There is no shared, inspectable, durable knowledge substrate underneath any of them.

| Today's approach | The problem |
|---|---|
| **Video summarizers** | Produce lossy prose consumed once and discarded. Re-ask a different question: full reprocess. |
| **Video QA systems** | Operate per-question against raw video. Nothing persists. Nothing is reusable. |
| **Cloud video APIs** (Twelve Labs, etc.) | Lock derived structure inside a paid account. The index is not yours. You cannot `git diff` it. |
| **General multimodal SDKs** | Serve models. No concept of a *scene*, *OCR overlap*, or a compiled artifact. One layer below where `vindex` operates. |

`vindex` treats video understanding as a **compilation problem** — deterministic, cacheable, versioned — not a generation problem. That is a categorically different engineering discipline.

---

## What it produces

A single `vindex compile video.mp4` run produces:

| Artifact | Description |
|---|---|
| `visual_memory.json` | The primary output — full compiled index of all extracted knowledge |
| `visual_memory.md` | Human-readable Markdown narration of the compiled facts |
| `timeline.json` | Ordered sequence of shots and scenes across the full video |
| `scene_index.json` | Semantically grouped shots with captions and metadata |
| `asr.json` | Full transcript with word-level timestamps and confidence scores |
| `ocr.json` | All on-screen text, timestamped and spatially positioned |

All JSON artifacts are validated against **versioned Pydantic schemas**. Schema version is embedded in every artifact. Output is byte-reproducible for the same video, config, and model versions.

---

## Use cases

| Use case | How vindex helps |
|---|---|
| **AI Coding Agents** | Give an agent a compiled `visual_memory.md` instead of raw video — it understands the video immediately, without any video-specific tooling. |
| **Video editing automation** | Know exactly where every cut, scene change, speaker action, and on-screen text occurs — before touching a single editing timeline. |
| **Content search and indexing** | Index thousands of videos as plain JSON. Search, filter, and diff them with standard tooling. No database server needed. |
| **Lecture / tutorial analysis** | Extract every slide's OCR text, every spoken word with timestamps, and every visual transition from a recording. |
| **RAG pipelines over video libraries** | Feed `visual_memory.json` directly into a vector store or LLM context. No custom video-ingestion pipeline to build. |
| **Research and journalism** | Audit and cite exactly what a video contains. Every extracted fact is timestamped, sourced, and reproducible. |
| **Multilingual video understanding** | Auto-detect and transcribe Hindi, English, Hinglish, and 99+ other languages with no configuration. |

---

## Architecture

```
Video File (.mp4, .mov, …)
        │
        ├── Scene / Shot Detection    ──►  PySceneDetect
        ├── Frame Extraction          ──►  PyAV (libavcodec)
        ├── Audio Extraction          ──►  ffmpeg
        ├── Speech Recognition (ASR)  ──►  faster-whisper (multilingual, auto-detect)
        ├── OCR (On-screen text)      ──►  PaddleOCR-VL (109 languages, CPU-only)
        └── VLM Scene Captioning      ──►  Qwen2-VL via mlx-vlm (Apple Silicon native)
                │
                │  Each extractor emits a typed Observation stream
                ▼
           ┌─────────────┐
           │  COMPILER   │  Deterministic merge of all Observations →
           │             │  Shots, Scenes, Timeline, Events
           └──────┬──────┘
                  │
           ┌──────▼──────────┐
           │ NARRATION LAYER │  LLM-grounded Markdown — phrases facts, never invents them
           └──────┬──────────┘
                  │
           ┌──────▼──────────┐
           │ REST API / CLI  │  FastAPI server + Typer CLI + single-page web UI
           └─────────────────┘
```

Every extraction stage is **independently replaceable** via a clean plugin interface. Swap out any model or runtime without touching the rest of the pipeline.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full pipeline design.

---

## Technology stack

| Category | Technology | Why |
|---|---|---|
| **Speech Recognition** | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (medium, 769M params) | CTranslate2-based; 99 languages; auto language detection; word-level timestamps |
| **OCR** | [PaddleOCR-VL](https://github.com/PaddlePaddle/PaddleOCR) (0.9B) | Outperforms classical OCR on stylized/burned-in video text; CPU-only; 109 languages |
| **Vision-Language Model** | [Qwen2-VL](https://huggingface.co/Qwen) via [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) | Native Apple Silicon (MLX); unified memory; best RAM-to-quality ratio on M-series |
| **Scene Detection** | [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | De-facto open-source standard; BSD-3; deterministic; no GPU dependency |
| **Video Decoding** | [PyAV](https://github.com/PyAV-Org/PyAV) | Direct libavcodec bindings; memory-efficient; supports all ffmpeg-compatible codecs |
| **Schema Validation** | [Pydantic v2](https://docs.pydantic.dev) | Runtime validation is load-bearing; JSON Schema export for non-Python consumers |
| **REST API** | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) | Async; auto-generated OpenAPI docs; consumed by any coding agent via HTTP |
| **CLI** | [Typer](https://typer.tiangolo.com) | Type-hint-driven; shares Pydantic models with SDK; self-documenting |
| **Embeddings** | [sentence-transformers](https://www.sbert.net) (MiniLM-L6-v2) | Local; CPU-compatible; used for semantic scene grouping |
| **Packaging** | [uv](https://github.com/astral-sh/uv) + [hatchling](https://hatch.pypa.io) | Fast installs; modern Python packaging standard (2025–2026) |
| **Testing** | pytest + [syrupy](https://github.com/syrupy-org/syrupy) (snapshot tests) | Schema drift caught by golden-fixture snapshot tests in CI |

---

## Minimum hardware requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| **OS** | macOS 13+ (Apple Silicon) | macOS 14+ (M2 or later) |
| **RAM** | 8 GB unified memory | 16 GB unified memory |
| **Storage** | 10 GB free (models + artifacts) | 20 GB free |
| **Python** | 3.11+ | 3.12 |
| **ffmpeg** | Required (system install: `brew install ffmpeg`) | Latest stable |

> **Linux support:** The pipeline runs on Linux with CPU-based inference. Replace `mlx-vlm` with a `llama.cpp` runtime plugin for NVIDIA GPU acceleration. See [ARCHITECTURE.md](ARCHITECTURE.md) for the plugin interface.

> **GPU:** No dedicated GPU required. All default runtimes run on CPU or Apple's Metal GPU via the unified memory architecture. No CUDA dependency.

### Model weights (downloaded once, stored locally at `~/.vindex/models/`)

| Model | Size on disk | Purpose |
|---|---|---|
| `faster-whisper-medium` | ~1.5 GB | Speech recognition (99 languages) |
| `Qwen2-VL-2B-Instruct-4bit` | ~1.3 GB | Scene captioning & narration (4-bit quantised) |
| `all-MiniLM-L6-v2` | ~90 MB | Text embeddings for scene grouping |
| PaddleOCR-VL detection + recognition | ~500 MB | On-screen text extraction |

**Total model footprint: ~3.5 GB.** All models download once and are reused across every subsequent run.

---

## Quick start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/your-org/vindex.git
cd vindex

# Install with uv (recommended)
pip install uv
uv sync

# Or install directly via pip
pip install vindex
```

### 2. Install ffmpeg (required system dependency)

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

### 3. Download model weights (one-time, ~3.5 GB)

```bash
uv run python scripts/download_weights.py
```

### 4. Start the API server and web UI

```bash
uv run uvicorn vindex.api.app:app --host 127.0.0.1 --port 8000
```

Open **`http://localhost:8000`** in your browser to use the built-in web UI — drag-and-drop a video and get the full compiled analysis back.

### 5. Compile a video via CLI

```bash
vindex compile lecture.mp4
```

Output artifacts appear alongside the video:

```
lecture/
├── visual_memory.json   ← primary compiled index
├── visual_memory.md     ← human-readable narration
├── timeline.json
├── scene_index.json
├── asr.json
└── ocr.json
```

### 6. Use the Python SDK

```python
from vindex import compile_video

index = compile_video("lecture.mp4")

for scene in index.timeline.scenes:
    print(scene.id, scene.caption, scene.start_ms, scene.end_ms)
```

### 7. Use the REST API from any coding agent

```bash
# Submit a video for compilation
curl -X POST http://localhost:8000/api/compile \
  -F "video=@lecture.mp4"
# → {"job_id": "abc123", "status": "processing"}

# Poll for completion
curl http://localhost:8000/api/jobs/abc123/status

# Fetch the compiled narration
curl http://localhost:8000/api/jobs/abc123/narration
```

The REST API is fully documented via the auto-generated OpenAPI spec at `http://localhost:8000/docs`.

---

## Design principles

- **Local-first by default.** No network calls. No API keys. No data leaves your machine.
- **Deterministic.** Same video + same config + same model version = byte-identical output, every time.
- **Plugin-based.** Every extractor sits behind a shared interface. Swap a model without forking the pipeline.
- **Versioned schemas.** Output artifacts carry a `schema_version`. Breaking changes are never silent.
- **Facts, not opinions.** The compiler surfaces what a video contains. Editorial judgment belongs to the consumer.
- **Compiler, not assistant.** `vindex` does not answer questions about videos. It compiles them. Answering questions is the consumer's job.

---

## Who it is for

| Audience | Why vindex |
|---|---|
| **AI Engineers** | Feed `visual_memory.json` into any LLM, RAG pipeline, or agent. No custom video-ingestion code to write. |
| **Software Engineers** | Local-first SDK. No cloud bill. No API key. Plain JSON on disk. Clean REST API for agent integration. |
| **Content Creators & Video Editors** | Know exactly what your video contains — every word, scene, and on-screen text — programmatically, before editing. |
| **Researchers** | Deterministic pipeline. Independently ablatable stages. Citable, versioned, auditable output. |
| **Product Teams** | Ship video-understanding features without rebuilding frame extraction, OCR, and scene detection from scratch. |

---

## Project status

**Active development — v0.1.0 (pre-release).**

| Phase | Description | Status |
|---|---|---|
| 0 | Foundation — schemas, interfaces, CI | ✅ Complete |
| 1 | Extractor layer — ASR, OCR, VLM, scene detection, frame extraction | ✅ Complete |
| 2 | Compiler — shot assembly, scene grouping, timeline construction | 🔄 In progress |
| 3 | Narration layer — LLM-grounded Markdown generation | ✅ Complete |
| 4 | CLI and Python SDK | 🔄 In progress |
| 5 | Plugin system and documentation | 🔄 In progress |
| 6 | Evaluation harness | ✅ Complete |

See [PROJECT_STATE.md](PROJECT_STATE.md) for detailed status and known gaps.

---

## Documentation

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Pipeline design, plugin system, canonical terminology |
| [TECH_STACK.md](TECH_STACK.md) | Every technology decision with full rationale and trade-offs |
| [ROADMAP.md](ROADMAP.md) | Phased implementation plan with milestones and dependencies |
| [VISION.md](VISION.md) | Long-term philosophy, first principles, non-goals |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute — setup, conventions, PR expectations |
| [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md) | Non-negotiable constraints that will never be compromised |
| [GLOSSARY.md](GLOSSARY.md) | Canonical terminology used across the codebase |

---

## Contributing

Contributions are welcome. The pipeline is cleanly modular — you can own exactly one extractor stage, add a new runtime plugin, or improve the compiler without touching anything else.

See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## License

[MIT](LICENSE)
