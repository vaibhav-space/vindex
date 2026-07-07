# TECH_STACK.md — vindex

This document records every major technology decision for `vindex`, with rationale. "We use X" is never sufficient — every choice documents why, what was considered, what was traded away, Apple Silicon compatibility, and long-term maintenance risk.

Changes to these decisions require an Architecture Decision Record in `/docs/adr/`.

---

## Scene and Shot Detection

**Chosen: PySceneDetect**

PySceneDetect is the de-facto open-source standard for content-aware shot boundary detection.

- **Why:** BSD-3 licensed, zero GPU dependency, deterministic output, active community, widely cited in academic and production work. This is a solved problem — reinventing it adds no value.
- **Alternatives:**
  - *TransNetV2* — neural, meaningfully more robust on fast cuts, whip-pans, and fades-to-black. Appropriate as an opt-in plugin for motion-graphics-heavy content. Not the default because it adds a model dependency where a non-neural tool suffices.
  - *ffmpeg native `scdet` filter* — zero Python dependency. Appropriate as a minimal fallback for environments where PySceneDetect cannot be installed. Lower accuracy on complex cuts.
- **Apple Silicon:** No GPU requirement. Runs on any hardware.
- **Maintenance:** Actively maintained, well-documented. Safe permanent dependency.

---

## Frame Extraction and Video Decoding

**Chosen: PyAV**

PyAV provides direct Python bindings to libavcodec/libavformat — the same codecs that power ffmpeg — without per-frame subprocess overhead.

- **Why:** More memory-efficient than OpenCV for sequential-then-random access patterns. Avoids the latency of spawning ffmpeg subprocesses per frame. Works with any codec ffmpeg supports.
- **Alternatives:**
  - *OpenCV VideoCapture* — simpler API, fine for lower-throughput use cases. Adds a large dependency for a problem PyAV solves more precisely.
  - *decord* — fast random access, minimal overhead. Flagged as a maintenance risk: check commit activity before depending on it. Not chosen as default due to uncertain long-term maintenance.
- **Apple Silicon:** PyAV links against libav compiled for arm64. Native support on M-series.
- **Maintenance:** Actively maintained. The underlying libav is permanent infrastructure.

---

## Audio Extraction

**Chosen: ffmpeg (direct)**

Audio extraction is a solved, trivial step with ffmpeg. Adding any other tool as an abstraction layer adds dependency cost for no benefit.

- **Why:** ffmpeg is an unavoidable dependency regardless. Invoking it directly for audio extraction requires no additional Python package.
- **No alternatives considered:** This decision requires no further justification.

---

## Speech Recognition (ASR)

**Chosen: whisper.cpp**

whisper.cpp is a C++ port of OpenAI Whisper with Metal acceleration for Apple Silicon.

- **Why:** Metal-accelerated on M-series, mature and widely deployed, active community, no Python runtime required for the core model. The SDK accepts an external transcript (with word-level timestamps) as an input contract — whisper.cpp is the default when no transcript is supplied, making the standalone SDK genuinely usable without requiring external tooling.
- **Alternatives:**
  - *WhisperKit* — Swift-native, highest raw throughput on M-series. Appropriate if a native Apple platform SDK is built in the future. Not appropriate as a Python SDK default due to Swift toolchain dependency.
  - *faster-whisper* — CTranslate2-based, strong cross-platform CPU fallback for non-Mac environments. Appropriate as a plugin for Linux contributors.
- **Apple Silicon:** Primary target. Metal acceleration provides significant speedup.
- **Maintenance:** Mature, actively maintained.
- **Note:** ASR is a first-class input, not just a pipeline stage. The SDK must accept an existing transcript as an input without running ASR at all. This is critical for users who have already transcribed their video through other means.

---

## OCR (On-Screen Text Extraction)

**Chosen: PaddleOCR-VL (0.9B)**

PaddleOCR-VL is a vision-language OCR model that significantly outperforms classical OCR on video content (stylized fonts, burn-in captions, slides, lower-thirds).

- **Why:** Meaningfully better than asking a general VLM to transcribe dense on-screen text — OCR-specific training produces more accurate results. Cheap enough to run per keyframe. Supports 109 languages. Runs CPU-only without a GPU requirement. Strong benchmark scores (OmniDocBench).
- **Alternatives:**
  - *Tesseract* — the mature classical OCR standard. Weaker on stylized or burned-in video text. Appropriate as a fallback for simple slide-heavy content or as a lightweight mode.
  - *EasyOCR* — simpler API, lower accuracy ceiling. Appropriate for quick prototyping but not for production-quality extraction.
  - *Relying on the VLM for OCR* — the general VLM is capable of reading text, but this conflates two independently verifiable tasks. Dedicated OCR produces better accuracy and clearer separation of concerns.
- **Apple Silicon:** CPU-only. Runs on any hardware. No Metal/GPU dependency.
- **Maintenance:** Actively maintained by PaddlePaddle team. Large community.

---

## Vision-Language Model (VLM) Captioning

**Chosen: Qwen2.5-VL / Qwen3-VL via mlx-vlm**

Qwen's VLM series via the `mlx-vlm` inference layer provides the best documented RAM-to-quality balance on Apple Silicon for this use case.

- **Why:** Native MLX support — runs on Apple's unified memory architecture without VRAM/RAM split. Native video-clip input support (not just individual frames). Strong captioning and scene description quality. Replaceable via the RuntimePlugin interface.
- **Alternatives:**
  - *Gemma 3 QAT* — strong general reasoning, weaker OCR. Appropriate as an alternative plugin for text-heavy content where OCR is already handled separately.
  - *mlx-community VLM zoo (Molmo, InternVL2)* — viable swap-in options behind the same interface. The interface design must accommodate any of these without modification.
  - *BLIP-2 or dedicated captioning models* — explicitly rejected. A separate captioning model alongside a general VLM adds a model dependency with no proportional benefit. One capable VLM does both captioning and general scene understanding now. Every extra model is a maintenance and RAM liability.
- **Apple Silicon:** Primary optimization target. MLX provides native arm64 acceleration.
- **Maintenance:** Actively maintained by Alibaba. Strong open-source community. `mlx-vlm` actively maintained by the mlx-community.

---

## Scene Understanding (Shot-to-Scene Grouping)

**No third-party library exists for this.**

Scene grouping — assigning shots to semantically coherent scenes — is not a model import. It is a heuristic plus embedding-based clustering problem:

1. Compute caption embeddings for each shot
2. Group shots by embedding similarity + time proximity + ASR speaker continuity
3. Derive scene boundaries from grouping results

This is core, bespoke project logic. No mature open-source library solves this problem with the right semantics for the `vindex` use case. Coding agents must not waste time searching for a library. This is built in `/compiler`.

---

## Motion and Temporal Analysis

**Chosen: OpenCV optical flow (Farneback or Lucas-Kanade)**

Coarse camera-movement classification (static, pan, zoom, cut) is sufficient for V1. Optical flow provides this without a learned model.

- **Why:** Deterministic, CPU-only, cheap per-frame. For the classification granularity this SDK needs ("the camera is zooming in"), frame-perfect motion vectors are unnecessary overhead. Optical flow is sufficient and avoids adding a motion-model dependency.
- **Alternatives:** Learned motion models (RAFT, etc.) — higher precision, significant overhead. Appropriate as a plugin for use cases requiring frame-level motion analysis. Not the default.
- **Note:** Motion analysis is deferred to post-V1. The interface must be designed in V1 so the object detection and motion extractor plugins have a stable home.
- **Apple Silicon:** CPU-only. Runs on any hardware.

---

## Object Detection

**Deferred to post-V1. Interface designed in V1.**

**Chosen when implemented: YOLO-World**

YOLO-World provides fast, open-vocabulary object detection without requiring a predefined category list.

- **Why:** Open vocabulary is essential — the SDK should not be constrained to a fixed object taxonomy. YOLO-World is fast enough to run per-keyframe without prohibitive overhead.
- **Alternative:** Grounding DINO — higher precision, heavier. Appropriate as an opt-in "high fidelity" mode for use cases where precision matters more than throughput.
- **Why deferred:** Object detection is valuable but not blocking a useful V1. The extractor interface is designed now so the plugin has a stable home. Implementation follows demand.

---

## Text Embeddings

**Chosen: bge-small or nomic-embed-text (local, CPU/MLX)**

Local text embedding models for caption and transcript text, used in scene grouping and semantic search.

- **Why:** Both run comfortably local on CPU or MLX without a network call. Both have stable, widely-adopted APIs. Size-to-quality ratio is appropriate for semantic similarity tasks within a video (not a cross-corpus search problem).
- **Alternatives:** OpenAI embedding API — rejected outright for violating the local-first constraint. Sentence-Transformers — fine, heavier than needed for this scope.

---

## Image Embeddings

**Chosen: open_clip**

open_clip provides open-source CLIP model embeddings for frame-level semantic indexing.

- **Why:** Widely adopted, stable API, compatible with mlx-clip variants for Apple Silicon acceleration. The semantic index (post-V1) requires both text and image embeddings in the same space — CLIP models provide this natively.

---

## Vector Store (Semantic Search)

**Chosen: LanceDB**

LanceDB is an embedded, file-based vector store with a Rust core and no server process.

- **Why:** Matches the "library, not a service" philosophy exactly. A consumer should not need to run a database daemon to use the SDK. File-based storage aligns with the local-first, portable-output principles. Rust core provides performance without Python GIL constraints.
- **Alternatives:**
  - *Chroma* — also embeddable, reasonable alternative. Slightly less performant at scale.
  - *Weaviate / Milvus* — require a running service. Wrong shape for a distributable local SDK. Explicitly rejected.
  - *FAISS* — suitable for pure in-memory use, but no persistence. Requires wrapping for the artifact model.

---

## Output Schema Validation

**Chosen: Pydantic v2**

Pydantic v2 provides typed schema definitions, JSON Schema export, and validation that is load-bearing — not advisory.

- **Why:** The project's central guarantee is that its output validates against a stable, typed schema. Pydantic makes validation failures a hard error, not a logged warning. JSON Schema export allows downstream non-Python consumers to generate their own typed clients without depending on the Python package. Contributors already know it.
- **Alternatives:** dataclasses — no validation. marshmallow — older, less expressive. attrs — viable, less ecosystem adoption in AI tooling. None of these provide the combination of runtime validation + schema export that Pydantic v2 does.

---

## Configuration Management

**Chosen: TOML + pydantic-settings**

- **Why:** TOML is unambiguous, Python-ecosystem-native (same format as `pyproject.toml`), and resistant to implicit type coercion errors that YAML silently introduces. `pydantic-settings` loads TOML config into the same typed Pydantic models used throughout the codebase — no parallel untyped config surface.
- **Alternatives:** YAML — more common in ML tooling but more error-prone. JSON — unambiguous but poor human editability (no comments). INI — too limited.

---

## CLI Framework

**Chosen: Typer**

Typer is a CLI framework built on Click, driven by Python type hints.

- **Why:** CLI commands share the exact same typed Pydantic models as the Python SDK and compiler. No parallel untyped argument surface to maintain. Typer integrates naturally with Pydantic, producing self-documenting CLI commands with minimal boilerplate.
- **Alternatives:** Raw Click — more verbose, same underlying capability. argparse — standard library but verbose and untyped.

---

## Plugin Discovery

**Chosen: Python entry_points (importlib.metadata)**

The standard Python plugin discovery mechanism — the same one pytest, flake8, and Babel use.

- **Why:** Mature, well-understood, no custom plugin loader to build or maintain. Contributors from any Python OSS background already know this pattern. Plugins install themselves via their own `pyproject.toml` — no changes to the core package required.

---

## Python Packaging and Environment Management

**Chosen: uv (Astral) for environment management, hatchling as build backend**

- **Why:** uv has emerged as the fast-moving community default through 2025–2026. Significantly faster installs and CI runs than pip or Poetry. Hatchling is a clean, well-maintained build backend with no legacy complexity.
- **Alternatives:** Poetry — mature, more opinionated, slower. pip + setuptools — functional but slower and more manual. The speed difference in uv matters for contributor onboarding and CI latency.

---

## Logging

**Chosen: standard library `logging` + structlog**

- **Why:** A pipeline whose entire value proposition is "structured, inspectable output" should have structured, inspectable operational logs. Structlog provides JSON-formatted logs with consistent field schemas. This is philosophical consistency, not just a nice feature.
- **Alternatives:** Loguru — more ergonomic, less flexible for structured output. Rich logging — human-readable only, not machine-parseable.

---

## Testing

**Chosen: pytest + snapshot testing (syrupy or equivalent)**

- **Why:** The project's actual contract is its output schema. Snapshot tests that catch silent schema drift are more important here than in a typical application — a "passing" test that produces silently different output has violated the core product guarantee. Snapshot/golden-file tests must be treated as required testing patterns, not optional additions.
- **CI requirement:** Snapshot tests run in CI on every PR. A failing snapshot test against a golden fixture means the code is wrong — never "fix" the fixture to make the test pass without a documented reason.

---

## Benchmarking

**Chosen: pytest-benchmark + bespoke eval harness**

- pytest-benchmark for micro-benchmarks (per-stage latency, memory use).
- A bespoke eval harness in `/eval` scoring compiled output against hand-labeled golden video fixtures.
- **Why bespoke:** No existing OSS project benchmarks "video-understanding-pipeline structural accuracy" for this use case. The eval harness must be built early — abstract schemas alone do not provide a concrete notion of "correct." Golden fixtures do, and they must exist before the compiler is built.

---

## Documentation

**Chosen: MkDocs + Material theme**

- **Why:** The same documentation stack used by Pydantic, FastAPI, and Typer — the exact libraries this project depends on. Familiarity for the target contributor base. Strong search, versioning, and code block support.

---

## CI/CD

**Chosen: GitHub Actions**

Matrix testing across macOS (Apple Silicon runners) and Linux. Model weight download steps cached between runs. Release automation via `uv build` and PyPI trusted publishing.

---

## Model Runtimes

### Primary (Apple Silicon): MLX

**Chosen: MLX (`mlx-lm` + `mlx-vlm`)**

- **Why:** Native unified-memory architecture on M-series. No VRAM/RAM split — models can use the full available memory. Fastest current option for VLM inference on Apple Silicon. Actively developed by Apple.

### Portable fallback: llama.cpp

**Chosen: llama.cpp**

- **Why:** Supports Metal, CUDA, and CPU inference from a single binary. Appropriate for Linux and Windows contributors, and for deployment targets that are not Apple Silicon. vLLM is a viable alternative specifically for Linux+NVIDIA batch workloads.
- **Why this must be explicit:** The project's stated goal requires the model-runtime layer to be an interface, not a hard MLX dependency. Otherwise the project silently becomes Mac-only despite claiming otherwise. RuntimePlugin provides this abstraction.

### Local model serving

**Chosen: none**

The SDK is a library and CLI, not a long-running service. If a consumer wants an OpenAI-compatible endpoint, they run `mlx_vlm.server` or `llama.cpp`'s server directly. The SDK does not reimplement model serving. This is consistent with "compiler, not app" — compilers do not run as daemons.

---

## Caching

**Chosen: content-addressed local cache (diskcache or plain content-addressed directory)**

Cache key: `hash(video_content) + pipeline_stage + model_version + config_hash`

- **Why first-class from day one:** Caching is where the determinism principle pays off directly as a user-facing feature. Re-running the same video with the same config and model versions must cost nothing after the first run. This must be designed into the extractor interface from the beginning — retrofitting a cache onto a non-cache-aware pipeline is significantly harder and produces worse cache coherence.
- **Why content-addressed:** Content addressing ensures the cache is valid for the same video regardless of filename or path. Two videos with identical content hash to the same cache key.
- **Why not a remote cache:** Violates local-first constraint. A remote cache is an opt-in plugin, never the default.
