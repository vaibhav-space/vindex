# ARCHITECTURE.md — vindex

This document describes the high-level system architecture of `vindex`. It is implementation-independent — it describes structure, data flow, and design decisions, not code.

For technology choices and rationale, see [TECH_STACK.md](TECH_STACK.md).
For canonical terminology definitions, see the Glossary section at the bottom of this document.
For non-negotiable constraints, see [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md).

---

## Mental Model

`vindex` is a compiler. Its input is a video file. Its output is a stable, typed, versioned artifact that any downstream system — human or AI — can consume without ever touching the original video again.

The analogy holds in detail:

| Compiler concept | vindex equivalent |
|---|---|
| Source file | Video file |
| Parse / lex | Frame extraction, audio extraction |
| Analysis passes | Extractors (scene detection, OCR, ASR, VLM captioning) |
| IR (intermediate representation) | `Observation` stream from each extractor |
| Linker / codegen | Compiler — merges Observations into structured artifacts |
| Output binary | `visual_memory.json` + `timeline.json` + supporting artifacts |
| Documentation layer | `visual_memory.md` — Markdown narration |

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────┐
│                    INPUT                            │
│              Video file (.mp4, .mov, …)             │
└─────────────────────────┬───────────────────────────┘
                          │
          ┌───────────────▼───────────────┐
          │         EXTRACTORS            │
          │  (run independently, in any   │
          │   order, against same input)  │
          │                               │
          │  ┌─────────────────────────┐  │
          │  │  Scene/Shot Detection   │  │
          │  └─────────────────────────┘  │
          │  ┌─────────────────────────┐  │
          │  │    Frame Extraction     │  │
          │  └─────────────────────────┘  │
          │  ┌─────────────────────────┐  │
          │  │    ASR (Transcript)     │  │
          │  └─────────────────────────┘  │
          │  ┌─────────────────────────┐  │
          │  │   OCR (On-screen text)  │  │
          │  └─────────────────────────┘  │
          │  ┌─────────────────────────┐  │
          │  │    VLM Captioning       │  │
          │  └─────────────────────────┘  │
          └───────────────┬───────────────┘
                          │
              Each extractor emits
              a stream of Observations
                          │
          ┌───────────────▼───────────────┐
          │           COMPILER            │
          │                               │
          │  Deterministic merge of all   │
          │  Observation streams into:    │
          │   - Shot list                 │
          │   - Scene groups              │
          │   - Timeline                  │
          │   - Events                    │
          │   - Relationships             │
          └───────────────┬───────────────┘
                          │
          ┌───────────────▼───────────────┐
          │       NARRATION LAYER         │
          │                               │
          │  LLM-grounded Markdown.       │
          │  Phrases compiled facts.      │
          │  Never invents new facts.     │
          │  Clearly isolated.            │
          └───────────────┬───────────────┘
                          │
          ┌───────────────▼───────────────┐
          │         OUTPUT ARTIFACTS      │
          │                               │
          │  visual_memory.json           │
          │  visual_memory.md             │
          │  timeline.json                │
          │  scene_index.json             │
          │  ocr.json                     │
          │  asr.json                     │
          └───────────────────────────────┘
```

---

## Core Concepts

### Extractor

An extractor is a single, independently executable stage that reads a video (or audio, or previously extracted frames) and emits a stream of `Observation` objects. Extractors are:

- Independent — no extractor may depend on another extractor's internals
- Replaceable — each implements a shared `Extractor` interface
- Deterministic — same inputs and config produce identical `Observation` streams
- Testable in isolation — given a known input, produce a known output

The five extractors in V1:
1. **SceneDetector** — identifies shot boundaries; emits Shot Observations
2. **FrameExtractor** — samples keyframes per shot; emits Frame Observations
3. **ASRExtractor** — transcribes audio with word-level timestamps; emits Word Observations
4. **OCRExtractor** — detects and transcribes on-screen text per keyframe; emits OCR Observations
5. **VLMCaptioner** — generates natural language captions per shot/keyframe via a vision-language model; emits Caption Observations

### Observation

An `Observation` is the atomic unit of knowledge emitted by an extractor. It represents exactly one thing one stage noticed at one point in time:

- One OCR reading at one location in one frame
- One detected shot boundary at one timestamp
- One ASR word at one timestamp
- One VLM caption for one shot

`Observation` is borrowed from sensor and robotics vocabulary, where the word has a precise, single-reading meaning. This is intentional — it reinforces that extractors are sensors, not interpreters.

### Compiler

The compiler receives all `Observation` streams and performs deterministic merge and grouping:

1. **Shot assembly** — organizes frame and shot boundary observations into a coherent Shot list
2. **Scene grouping** — groups shots into semantic scenes by combining caption-embedding similarity, time proximity, and ASR speaker continuity
3. **Event derivation** — derives named Events from observation patterns (e.g., "speaker change," "slide transition")
4. **Relationship resolution** — identifies spatial and temporal relationships between Observations (e.g., OCR text overlapping a graph within the same shot)
5. **Timeline construction** — assembles the final ordered spine of Scenes and Events

The compiler is the most product-IP-dense part of the system. Scene grouping (step 2) is custom logic — there is no mature open-source library that solves this problem. It is not a model import; it is heuristic plus embedding-based clustering. See [TECH_STACK.md](TECH_STACK.md) for the approach.

### Narration Layer

The narration layer takes the fully compiled JSON artifacts and generates `visual_memory.md` — a human-readable Markdown document describing the video's contents.

**Critical architectural boundary:** the narration layer is physically and conceptually separated from the compiler. It lives in `/narration`, not `/compiler`. This separation enforces — as a structural fact about the repository — that facts are compiled deterministically in one place and phrased by an LLM in another. The narration layer:

- May only read from compiled JSON artifacts
- Must never introduce facts not present in those artifacts
- Is the one explicitly non-deterministic stage in the pipeline
- Must be clearly labeled as such in its output

### Output Artifacts

All output artifacts are versioned JSON validated against Pydantic schemas. Every artifact embeds its `schema_version` field. Schema changes require an explicit version bump and a migration note.

| Artifact | Contents |
|---|---|
| `visual_memory.json` | Top-level compiled index; references all sub-artifacts |
| `timeline.json` | Ordered Scenes and Events; the navigational spine |
| `scene_index.json` | One entry per Scene with shots, captions, duration, ASR text |
| `ocr.json` | All on-screen text observations with bounding boxes and timestamps |
| `asr.json` | Full transcript with word-level timestamps |
| `visual_memory.md` | Human-readable narration; derived from JSON, not primary |

---

## Plugin Architecture

Every replaceable component is exposed behind a typed interface. There are two levels of plugin:

### Extractor Interface

`Extractor` is the abstract base class all extraction stages implement. An extractor accepts a video path and a config dict, and emits a stream of `Observation` objects. All extractors are independently testable in isolation.

### Typed Runtime Interfaces

Every inference category has its own typed abstract interface. Extractors consume these interfaces via constructor injection — never by importing concrete model libraries directly. Only files in `/runtimes/` may import concrete libraries.

| Interface | Responsibility | V1 Implementation |
|---|---|---|
| `ASRRuntime` | Audio → word-level transcript | `FasterWhisperRuntime`, `WhisperCppRuntime` |
| `OCRRuntime` | Frame image → text regions with bounding boxes | `PaddleOCRRuntime` |
| `VisionRuntime` | Frame image(s) + prompt → caption string | `MLXVLMRuntime` (Qwen2.5-VL) |
| `EmbeddingRuntime` | Text list → dense vectors | `MiniLMEmbeddingRuntime` |
| `LLMRuntime` | Prompt → generated text (narration layer only) | shares `MLXVLMRuntime` |

**Dependency injection rule:** Every extractor's `__init__` accepts its runtime as a constructor argument. The compiler wires extractors and runtimes together at startup. This means:
- Extractors are testable with mocked runtimes — no model weights needed in CI
- Swapping a runtime (e.g., replacing `MLXVLMRuntime` with an `OllamaRuntime`) requires zero changes to the extractor
- New runtime implementations (CUDA, Transformers, API-backed with opt-in) can be added as third-party plugins without touching the core package

### Output Plugins

`OutputPlugin` handles writing compiled artifacts to a specific format or destination. The default output is plain JSON files to a local directory. Additional output plugins (e.g., CBOR format, SQLite-backed output) register via Python `entry_points`.

### Plugin Discovery

All plugin categories use Python `entry_points` (the standard `importlib.metadata` mechanism — the same one pytest and flake8 use for plugin discovery):

```toml
# In a plugin package's pyproject.toml
[project.entry-points."vindex.extractors"]
faster_whisper = "my_plugin:FasterWhisperRuntime"
```

This means:
- No custom plugin loader to build or maintain
- Contributors from any Python OSS background already know this pattern
- A plugin installs itself via its own `pyproject.toml` — no changes to the core package required

---

## Caching

The caching layer is a first-class architectural component, not a bolt-on optimization.

Cache key: `hash(video_content) + pipeline_stage + model_version + config_hash`

This key is deterministic by design — the same computation always produces the same cache key. Re-running the same video with the same config and model versions costs nothing after the first run. Cache entries are stored in a content-addressed local directory (`diskcache` or equivalent).

Caching is the point at which the determinism principle pays off directly as a user-facing feature. It should be designed into the extractor interface from day one, not retrofitted after V1.

---

## Repository Structure

```
/core           — Pydantic schemas. The contract. Read here first.
/extractors     — One subfolder per stage. Each implements Extractor.
/compiler       — Deterministic merge logic. Heaviest test coverage.
/narration      — LLM-driven Markdown generation. Isolated by design.
/runtimes       — Model backend adapters (MLX, llama.cpp, etc.).
/cli            — Thin Typer wrappers. No business logic.
/plugins        — Reference plugins and entry_points documentation.
/eval           — Golden video set, scoring harness, benchmark results.
/docs           — Documentation mirroring the folder structure above.
```

**Why this structure scales:** as new extractors are added over years, they land at the same depth (`/extractors/<name>/`, `/docs/extractors/<name>.md`). The tree's shape never needs to change as scope grows — only its width.

---

## Design Principles

**Independence over coupling.** No extractor may import or depend on another extractor. If this cannot be enforced by folder discipline alone, an import-linter rule enforces it in CI.

**Schema before code.** Every extractor's job is defined entirely by "which Observation schema does my output validate against?" Schemas are written and reviewed before any extractor code exists.

**Build order matters.** Schemas before extractors. Extractors before the compiler. The compiler before narration. Narration before CLI polish. Building visible parts before the foundational parts is the most common way a project of this structure goes sideways.

**The narration layer never invents.** If a fact does not appear in the compiled JSON, the narration layer has no right to assert it. Any narration claim must be traceable to a specific `Observation` or derived `Event` in the compiled output.

---

## Glossary

These terms are canonical across the entire project. All schema field names, class names, and documentation must use these terms exactly.

| Term | Definition |
|---|---|
| **Shot** | A single continuous camera take between two cuts. The raw unit output by scene detection tools. Never derived. |
| **Scene** | A semantically coherent group of one or more Shots. Always derived by the compiler — never raw. |
| **Segment** | An abstract, generic time-range container used as the base type when the Shot/Scene distinction does not matter. Used in schema and interface design; not user-facing. |
| **Observation** | The atomic fact unit emitted by an extractor: one OCR reading, one shot boundary, one ASR word, one VLM caption. One thing one stage noticed at one point in time. |
| **Event** | A specific, named occurrence derived from one or more Observations (e.g., "speaker change," "slide transition"). One level of interpretation above a raw Observation. |
| **Relationship** | A structured link between two Observations, Entities, or Events (e.g., caption-overlaps-graph, speaker-mentions-entity). |
| **Entity** | A named thing with a stable ID recognized across scenes (a person, a logo, a recurring on-screen element). The anchor that makes Relationships possible across time. |
| **Timeline** | The ordered spine of Shots, Scenes, and Events across the whole video. The master index other artifacts reference by position. |
| **Clip** | Reserved exclusively for rendered, byte-level video output — an actual exported mp4 sub-range. Never use "Clip" for metadata-only time ranges. |
| **Frame Group** | Internal-only term for the sampled keyframes representing one Shot. Not user-facing. |
| **visual_memory.json** | The top-level compiled output artifact. The product-facing name. Internal class and module names use Index, not Memory. |

**Terms to avoid:**

- **Moment** — too vague, too marketing-flavored. Avoid in code and schemas.
- **Memory** (as an internal class or module name) — reserved for the product-facing filename only. Internal names use `Index` and `Observation`/`Event`. This prevents contributors from accidentally importing mutable-agent-memory semantics (decay, merge, forget) into what must remain a stable, re-derivable compilation artifact.

**Recommended mental hierarchy:**

```
Shot (raw)
  └── Scene (compiled group of Shots)
        └── Timeline (ordered sequence of Scenes and Events)

Observations attach at the Shot/Scene level.
Observations roll up into Events and Relationships.
Events and Relationships are anchored by persistent Entity identities.
```
