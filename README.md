# vindex

**The open-source video knowledge compiler.**

> Compile any video, once, into a deterministic, inspectable, versioned knowledge artifact — so no AI system ever has to watch the same video twice.

Think of it as Tesseract, but for everything a video contains — not just the text in it.

---

## What it is

`vindex` is a local-first Python SDK and CLI that processes a video file through a modular extraction pipeline and produces stable, typed, versioned output artifacts — structured JSON and Markdown — that any downstream system can consume without ever touching the original video again.

It is a **compiler**, not an assistant. It produces **facts**, not opinions. It runs **entirely on your machine** and calls no external service by default.

---

## The problem it solves

Every AI system that touches video today re-derives understanding from scratch — non-reproducibly, at cost, every time. There is no shared, inspectable, durable substrate underneath any of them.

- **Video summarizers** produce lossy prose consumed once and discarded. Re-ask a different question: full reprocess.
- **Video QA systems** operate per-question against raw video every time. Nothing persists. Nothing is reusable.
- **Cloud video APIs** (Twelve Labs, etc.) lock the derived structure inside a paid account. The index is not yours. You cannot `git diff` it.
- **General multimodal SDKs** serve models. They have no concept of a *scene*, *OCR overlap*, or a compiled artifact. They are one layer below where `vindex` operates.

`vindex` treats video understanding as a **compilation problem** — deterministic, cacheable, versioned — not a generation problem. That is a categorically different engineering discipline.

---

## What it produces

A single run of `vindex compile video.mp4` produces:

| Artifact | Description |
|---|---|
| `timeline.json` | Ordered sequence of shots and scenes across the full video |
| `scene_index.json` | Semantically grouped shots with captions and metadata |
| `ocr.json` | All on-screen text, timestamped and positioned |
| `asr.json` | Full transcript with word-level timestamps |
| `visual_memory.json` | Top-level compiled index — the primary output artifact |
| `visual_memory.md` | Human-readable Markdown narration of the compiled facts |

All JSON artifacts are validated against versioned schemas. Schema version is embedded in every artifact. Output is byte-reproducible for the same video, config, and model versions.

---

## Architecture overview

```
Video File
    │
    ├── Scene / Shot Detection   (PySceneDetect)
    ├── Frame Extraction         (PyAV)
    ├── ASR                      (whisper.cpp)
    ├── OCR                      (PaddleOCR-VL)
    └── VLM Captioning           (Qwen2.5-VL via mlx-vlm)
            │
            ▼
        Compiler
      (deterministic merge of Observations into Scenes, Timeline, Events)
            │
            ▼
     Narration Layer
   (LLM-grounded Markdown — isolated, clearly labeled non-deterministic)
            │
            ▼
    Output Artifacts
```

Every extraction stage is independently replaceable via the plugin interface. The compiler is the only place stages are joined. The narration layer is physically and architecturally separate from the compiler — it phrases facts, never invents them.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full pipeline design.

---

## Quick example

```bash
# Install
pip install vindex

# Compile a video
vindex compile lecture.mp4

# Output lives alongside the video by default
ls lecture/
  timeline.json
  scene_index.json
  ocr.json
  asr.json
  visual_memory.json
  visual_memory.md
```

```python
from vindex import compile_video

index = compile_video("lecture.mp4")

for scene in index.timeline.scenes:
    print(scene.id, scene.caption, scene.start_ms, scene.end_ms)
```

---

## Who it is for

| Audience | Why vindex |
|---|---|
| **Software Engineers** | Local-first SDK. No cloud bill. No API key. Plain JSON on disk. |
| **AI Researchers** | Deterministic pipeline. Independently ablatable stages. Citable, versioned output. |
| **Product Teams** | Ship video-understanding features without rebuilding frame extraction, OCR, and scene detection from scratch. |
| **Open Source Contributors** | Cleanly modular pipeline. Own exactly one stage. Small, legible PR scope. |

---

## Design principles

- **Local-first by default.** No network calls unless explicitly configured.
- **Deterministic.** Same video + same config + same model version = byte-identical output.
- **Plugin-based.** Every extractor sits behind a shared interface. Swap without forking.
- **Versioned schemas.** Output artifacts carry a `schema_version`. Breaking changes are never silent.
- **Facts, not opinions.** The compiler surfaces what a video contains. Editorial judgment belongs to the consumer.
- **Compiler, not assistant.** `vindex` does not answer questions about videos. That is the consumer's job.

See [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md) for the non-negotiable constraints this project will never compromise.

---

## Current status

**Pre-release. Active development.**

See [PROJECT_STATE.md](PROJECT_STATE.md) for the current milestone, completed work, and known gaps.
See [ROADMAP.md](ROADMAP.md) for the full implementation plan.

---

## Documentation

| File | Purpose |
|---|---|
| [VISION.md](VISION.md) | Long-term philosophy, first principles, non-goals |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Pipeline design, plugin system, canonical terminology |
| [TECH_STACK.md](TECH_STACK.md) | Every technology decision with rationale and trade-offs |
| [ROADMAP.md](ROADMAP.md) | Phased implementation plan with milestones and dependencies |
| [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md) | Non-negotiable constraints |
| [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) | Completion criteria for every milestone and module |
| [AGENT_RULES.md](AGENT_RULES.md) | Rules every coding agent must follow |
| [PROJECT_STATE.md](PROJECT_STATE.md) | Living project tracker — current status and known debt |

---

## License

MIT