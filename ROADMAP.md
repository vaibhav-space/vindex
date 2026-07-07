# ROADMAP.md — vindex

This roadmap defines the phased implementation plan for `vindex`. It is written for coding agents and human contributors alike. Each phase lists its deliverables, dependencies, and completion criteria. A phase does not begin until its dependencies are complete.

For what "complete" means for any individual module, see [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md).
For the current state of each phase, see [PROJECT_STATE.md](PROJECT_STATE.md).
For non-negotiable scope boundaries, see [VISION.md](VISION.md) and [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md).

---

## Build Order Principle

**Schemas before extractors. Extractors before the compiler. Compiler before narration. Narration before CLI polish.**

Building visible parts (CLI, narration output) before the foundational parts (schemas, extractors, compiler) is the most common way a modular pipeline project goes sideways. This order is not a suggestion.

---

## Phase 0 — Foundation

**Purpose:** Establish every ground-truth artifact that coding agents use as reference during all subsequent phases. No extraction logic. No model invocations. Nothing that processes a video.

**Dependency:** None. This phase begins immediately.

### Deliverables

- [ ] Repository structure created (`/core`, `/extractors`, `/compiler`, `/narration`, `/runtimes`, `/cli`, `/plugins`, `/eval`, `/docs`)
- [ ] `pyproject.toml` with project metadata, uv/hatchling build config, and empty dependency groups
- [ ] `GLOSSARY.md` — canonical terminology (mirrors the Glossary section of `ARCHITECTURE.md`; single source of truth)
- [ ] `SCOPE.md` — the V1 belongs/deferred/never lists as literal checkboxes; the primary scope-creep guardrail for agents
- [ ] `ASSUMPTIONS.md` — created empty; the designated place for agents to log undocumented decisions
- [ ] `SCHEMA_VERSIONING.md` — rules for how schemas are versioned and migrated (semantic versioning on schemas, `schema_version` field required on every artifact, no silent breaking changes, migration notes required)
- [ ] `REPO_MAP.md` — folder-by-folder index; agents always know exactly where new code belongs
- [ ] Draft Pydantic v2 schemas in `/core` for all V1 output artifacts:
  - `Observation` (base type)
  - `ShotObservation`
  - `FrameObservation`
  - `ASRWordObservation`
  - `OCRObservation`
  - `CaptionObservation`
  - `Shot`
  - `Scene`
  - `Event`
  - `Timeline`
  - `VisualMemory` (top-level artifact)
- [ ] JSON Schema exports for all above schemas in `/core/schemas/`
- [ ] `/eval/golden/` directory with at minimum two sample video files and hand-written expected `visual_memory.json` and `visual_memory.md` for each
- [ ] CI workflow (GitHub Actions) that runs linting and type checking (no tests yet — nothing to test)

### Completion criteria

All schema files validate against themselves. All JSON Schema exports are present. `/eval/golden/` contains at minimum two complete golden fixtures. CI passes. No extraction code exists.

---

## Phase 1 — Extractor Layer

**Purpose:** Implement the five V1 extractors, each independently testable against the schemas defined in Phase 0.

**Dependency:** Phase 0 complete. All schemas finalized and exported.

### Deliverables

Each extractor must ship as a complete unit (interface, tests, golden fixture, docs page) — no partial extractors merge.

#### 1.1 — Scene and Shot Detection Extractor

- [ ] `SceneDetector` extractor implementing the `Extractor` interface
- [ ] Uses PySceneDetect as the default backend
- [ ] Emits `ShotObservation` objects validated against the schema
- [ ] Unit tests with a synthetic or small real video fixture
- [ ] Golden fixture: known video → known shot list
- [ ] `/docs/extractors/scene_detection.md`

#### 1.2 — Frame Extraction Extractor

- [ ] `FrameExtractor` extractor implementing the `Extractor` interface
- [ ] Uses PyAV for frame access
- [ ] Deterministic keyframe sampling strategy per shot (e.g., middle frame, first/last frame — configurable)
- [ ] Emits `FrameObservation` objects validated against the schema
- [ ] Unit tests and golden fixture
- [ ] `/docs/extractors/frame_extraction.md`

#### 1.3 — ASR Extractor

- [ ] `ASRExtractor` extractor implementing the `Extractor` interface
- [ ] Accepts an existing transcript (JSON with word-level timestamps) as input — this is the primary mode
- [ ] Falls back to whisper.cpp when no transcript is provided
- [ ] Emits `ASRWordObservation` objects validated against the schema
- [ ] Unit tests and golden fixture
- [ ] `/docs/extractors/asr.md`

#### 1.4 — OCR Extractor

- [ ] `OCRExtractor` extractor implementing the `Extractor` interface
- [ ] Uses PaddleOCR-VL as the default backend
- [ ] Runs per-keyframe (receives `FrameObservation` stream as input)
- [ ] Emits `OCRObservation` objects with bounding boxes and timestamps, validated against the schema
- [ ] Unit tests and golden fixture
- [ ] `/docs/extractors/ocr.md`

#### 1.5 — VLM Captioning Extractor

- [ ] `VLMCaptioner` extractor implementing the `Extractor` interface
- [ ] Uses Qwen2.5-VL via mlx-vlm as the default backend
- [ ] Runs per-shot (receives `ShotObservation` + `FrameObservation` stream as input)
- [ ] Emits `CaptionObservation` objects validated against the schema
- [ ] RuntimePlugin interface finalized — VLM backend is swappable without touching extractor logic
- [ ] Unit tests and golden fixture
- [ ] `/docs/extractors/vlm_caption.md`

#### 1.6 — Caching Layer

- [ ] Content-addressed cache implemented, keyed by `hash(video_content) + stage + model_version + config_hash`
- [ ] Cache integrated at the extractor interface level — all extractors participate automatically
- [ ] Cache miss path: run extractor, write to cache. Cache hit path: return cached observations.
- [ ] Unit tests for cache correctness (same input → same cache key, different model version → different cache key)

### Completion criteria

All five extractors pass their unit tests and golden fixture tests. Each extractor's output validates against its schema. Caching works across all five extractors. CI passes.

---

## Phase 2 — Compiler

**Purpose:** Implement the deterministic compiler that merges Observation streams from all five extractors into the full set of output artifacts.

**Dependency:** Phase 1 complete. All extractors producing validated Observations.

### Deliverables

- [ ] `Shot` assembly — groups `ShotObservation` + `FrameObservation` + `ASRWordObservation` + `OCRObservation` + `CaptionObservation` into structured `Shot` objects
- [ ] `Scene` grouping — clusters shots into semantically coherent scenes using caption-embedding similarity + time proximity + ASR speaker continuity heuristics
- [ ] `Event` derivation — identifies named Events from observation patterns (speaker change, slide transition, etc.)
- [ ] `Relationship` resolution — identifies spatial and temporal relationships between observations (e.g., OCR text overlapping the same time window as a caption)
- [ ] `Timeline` construction — assembles the ordered spine of Scenes and Events
- [ ] `VisualMemory` assembly — top-level artifact combining all the above
- [ ] All outputs validate against their Pydantic schemas
- [ ] Golden fixture tests: feed known extractor outputs → verify known compiler outputs (tested against `/eval/golden/`)
- [ ] Comprehensive unit tests for each compiler step independently
- [ ] `/docs/compiler.md`

### Completion criteria

For each golden video fixture: feed all five extractor outputs into the compiler and verify the compiled `visual_memory.json`, `timeline.json`, and `scene_index.json` match the expected golden output within defined tolerance. CI passes. No narration code exists yet.

---

## Phase 3 — Narration Layer

**Purpose:** Implement the LLM-driven Markdown narration of the compiled artifacts.

**Dependency:** Phase 2 complete. Compiler produces valid `VisualMemory` artifacts.

### Deliverables

- [ ] `Narrator` class that reads a `VisualMemory` artifact and produces `visual_memory.md`
- [ ] Narrator is strictly grounded — it may only phrase facts present in the compiled JSON; it may never assert a fact not traceable to an Observation or derived Event
- [ ] Narrator is clearly labeled as non-deterministic in its output (the Markdown preamble notes the model and version used)
- [ ] RuntimePlugin for the narrator's LLM backend (defaults to the same VLM runtime used for captioning)
- [ ] Tests verify that narrator output contains no facts absent from the input JSON
- [ ] `/docs/narration.md`

### Completion criteria

For each golden video: the narrator produces a `visual_memory.md` that passes factual grounding verification (no invented claims). CI passes.

---

## Phase 4 — CLI and Python SDK

**Purpose:** Expose the full pipeline as a usable CLI and Python SDK.

**Dependency:** Phase 3 complete.

### Deliverables

- [ ] `vindex compile <video>` — runs the full pipeline and writes all output artifacts
- [ ] `vindex compile --stages scene,ocr,asr` — runs a subset of stages
- [ ] `vindex compile --transcript <file>` — accepts an existing transcript, skips ASR
- [ ] `vindex inspect <artifact>` — pretty-prints a compiled artifact
- [ ] `vindex validate <artifact>` — validates a JSON artifact against its schema
- [ ] Python SDK entry points (`from vindex import compile_video`)
- [ ] `--output-dir` flag for controlling output location
- [ ] `--config` flag for providing a TOML configuration file
- [ ] CLI help text is accurate and complete
- [ ] Python SDK is documented in `/docs/sdk.md`
- [ ] CLI is documented in `/docs/cli.md`
- [ ] End-to-end integration test: `vindex compile` on a golden video produces the expected artifacts

### Completion criteria

`vindex compile` on each golden video produces artifacts that pass schema validation and golden fixture comparison. CI passes.

---

## Phase 5 — Plugin System and Documentation

**Purpose:** Formalize the plugin interface, ship reference plugins, and complete the public documentation.

**Dependency:** Phase 4 complete.

### Deliverables

- [ ] `ExtractorPlugin` interface documented and stable
- [ ] `RuntimePlugin` interface documented and stable
- [ ] `OutputPlugin` interface documented and stable
- [ ] At least one reference plugin per category (e.g., a faster-whisper ASR plugin, a Tesseract OCR fallback plugin)
- [ ] Plugin discovery via Python `entry_points` verified working end-to-end
- [ ] `/docs/plugins/` — plugin authoring guide, interface contracts, examples
- [ ] MkDocs site builds successfully
- [ ] All public API surfaces have docstrings
- [ ] `CONTRIBUTING.md` — contributor guide covering setup, testing, and PR expectations

### Completion criteria

A third-party plugin can be installed and discovered without modifying the core package. Documentation site builds. CI passes.

---

## Phase 6 — Evaluation Harness

**Purpose:** Build the scoring harness that measures pipeline accuracy against hand-labeled golden fixtures, and run the first formal benchmark.

**Dependency:** Phase 4 complete. Can be developed in parallel with Phase 5.

### Deliverables

- [ ] Scoring harness in `/eval` — measures structural accuracy of compiled artifacts vs. golden fixtures
- [ ] Metrics defined and documented: scene boundary accuracy, OCR extraction recall/precision, ASR word error rate, caption semantic similarity
- [ ] Benchmark results for the default pipeline configuration stored in `/eval/results/`
- [ ] `vindex eval` CLI command runs the harness against all golden fixtures
- [ ] `/docs/eval.md` — evaluation methodology and how to contribute new golden fixtures

### Completion criteria

`vindex eval` runs to completion on all golden fixtures, produces a score report, and results are committed to `/eval/results/`.

---

## Deferred (Post-V1)

These items are in scope for the project but explicitly deferred until V1 is complete and stable.

- **Object detection** — `ObjectObservation`, YOLO-World backend, `object_index.json` artifact
- **Motion classification** — `MotionObservation`, OpenCV optical flow backend, `motion.json` artifact
- **Cross-scene entity tracking** — `Entity` schema, `EntityTracker` compiler step, `relationships.json` artifact
- **Semantic embeddings and vector search** — bge-small / nomic-embed-text text embeddings, open_clip image embeddings, LanceDB integration, `semantic_index.json` artifact
- **Multi-language narration** — narrator configuration for non-English output
- **Linux/NVIDIA performance optimization** — llama.cpp CUDA path, faster-whisper on GPU, performance benchmarks

None of these items may be started until V1 (Phases 0–5) is complete and PROJECT_STATE.md reflects that status.

---

## Architecture Decision Records

All significant decisions made during implementation must be recorded in `/docs/adr/`. This includes:

- Deviations from the choices in [TECH_STACK.md](TECH_STACK.md)
- Any scope changes
- Any schema breaking changes
- Any changes to the build order or milestone boundaries

ADR format: `/docs/adr/YYYY-MM-DD-<short-title>.md`
