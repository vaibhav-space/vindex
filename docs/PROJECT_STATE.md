# PROJECT_STATE.md — vindex

This is the living project tracker. It reflects the current state of the repository at all times. Future coding agents should be able to resume development using this file in combination with [ROADMAP.md](ROADMAP.md) and [AGENT_RULES.md](AGENT_RULES.md).

**Agents: update this file after completing any milestone. Never let it drift from reality.**

Last updated: 2026-11-08

---

## Current Status

**Phase:** Application-Ready & Core Hardened (Phases 0–6 Implemented, V0.2 Release Candidate)

**Summary:** The foundation, extractor layer, relationship resolution compiler, narration layer, evaluation harness, content-addressed caching, CLI (`compile`, `eval`, `inspect`, `validate`, `--stages`), REST API with Web Studio video preview, and plugin discovery system are fully implemented and passing all tests. Portable path handling and automated CI test pipelines are in place.

---

## Completed Milestones

### Documentation Foundation, Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, Phase 5 & Phase 6

- [x] Raw architecture document reviewed and synthesized
- [x] `README.md` — public landing page
- [x] `VISION.md` — mission, first principles, scope, non-goals
- [x] `ARCHITECTURE.md` — pipeline design, glossary, plugin system, repository structure
- [x] `TECH_STACK.md` — all technology decisions with full rationale
- [x] `ROADMAP.md` — phased implementation plan
- [x] `AGENT_RULES.md` — rules for coding agents
- [x] `PROJECT_CONSTRAINTS.md` — non-negotiable constraints
- [x] `DEFINITION_OF_DONE.md` — completion criteria
- [x] `PROJECT_STATE.md` — this file
- [x] Phase 0 Foundation — canonical package tree, pyproject.toml, glossary, scopes, Pydantic schemas, exported JSON Schemas, interfaces, and CI configurations
- [x] Phase 1 Extractor Layer — ASR, OCR, SceneDetector, FrameExtractor, and VLMCaptioner extractors and the content-addressed ObservationCache caching layer
- [x] Phase 2 Compiler Core — shot assembly, scene grouping, event derivation, timeline construction, and `RelationshipResolver` (spatial/temporal OCR-to-caption mapping)
- [x] Phase 3 Narration Layer — LLM-driven Markdown narrator (`Narrator`) and strict grounding prompt template
- [x] Phase 4 CLI & REST API — `vindex compile`, `inspect`, `validate`, `--stages`, `--config`, and FastAPI REST server with Web Studio UI & live video preview
- [x] Phase 5 Plugin Discovery — `vindex/core/plugins.py` dynamic loading via standard `importlib.metadata.entry_points` (`vindex.extractors`, `vindex.runtimes`, `vindex.outputs`)
- [x] Phase 6 Evaluation Harness — `vindex eval` CLI subcommand, scoring metrics, and pass/fail thresholds
- [x] Machine-Independent Portability — Environment-variable configurable paths (`VINDEX_MODELS_DIR`, `VINDEX_JOBS_DIR`, `PADDLEX_MODELS_DIR`) with user-home fallbacks
- [x] Weight Management Utility — `scripts/download_weights.py` with `--dry-run` and per-model flags

---

## Remaining Limitations & Future Work

- **Cross-scene multi-speaker diarization:** Speaker continuity across shot cuts relies on Whisper timestamps; acoustic clustering / voiceprint diarization is planned for v0.3.
- **Hardware constraints:** MLX-based VLM inference is optimized for Apple Silicon (macOS); Linux inference relies on CPU runtime or external llama.cpp plugin.
- **Object Detection & Motion Flow:** `object_index.json` (YOLO) and optical flow classification are prototyped in `vindex/runtimes/objects` and `vindex/runtimes/motion`, deferred from the default pipeline.
- **PyPI Distribution Namespace:** Distribution name is registered as `vindex-video` to avoid conflict with an existing unrelated PyPI package (`vindex`), while retaining `import vindex` in Python.

---

## Planned Milestones

See [ROADMAP.md](ROADMAP.md) for full details. Summary:

| Phase | Description | Status |
|---|---|---|
| 0 | Foundation — repository structure, governance files, schemas, golden fixtures | Completed |
| 1 | Extractor layer — SceneDetector, FrameExtractor, ASRExtractor, OCRExtractor, VLMCaptioner, caching | Completed |
| 2 | Compiler — shot assembly, scene grouping, event derivation, timeline, relationship resolver | Completed |
| 3 | Narration layer — grounded LLM Markdown generation | Completed |
| 4 | CLI and Python SDK — `vindex compile`, `inspect`, `validate`, `--stages`, REST API & Web Studio | Completed |
| 5 | Plugin system and documentation — entry_points loading, MkDocs | Completed |
| 6 | Evaluation harness — fixture comparison, Jaccard/F1 metrics | Completed |
| 7 | Cross-scene entity tracking & Acoustic Diarization | Planned (v0.3) |

---

## Architecture Decisions

All significant architecture decisions are documented here as a running log. Detailed ADRs belong in `/docs/adr/` once that directory exists.

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-08 | Project named `vindex` | Already the repository name; clean portmanteau of "video" + "index"; infra-sounding; short. |
| 2026-07-08 | Positioned as "open-source video knowledge compiler" | Avoids "Memory SDK" framing which conflates with mutable agent-memory systems (Mem0, Zep, Letta). The output is a compiled index, not stateful memory. |
| 2026-07-08 | Internal class names use `Index`, `Observation`, `Event` — not "Memory" | Prevents contributors from accidentally importing mutable-agent-memory semantics into what must remain a stable, re-derivable compilation artifact. |
| 2026-07-08 | VLM: Qwen2.5-VL via mlx-vlm (primary) | Best RAM/quality balance on Apple Silicon; native MLX; no separate captioning model needed. |
| 2026-07-08 | OCR: PaddleOCR-VL (0.9B) | Dedicated OCR model outperforms general VLM on dense on-screen text; CPU-only; 109 languages. |
| 2026-07-08 | ASR: whisper.cpp | Metal-accelerated; accepts external transcript as primary input; falls back to local when none supplied. |
| 2026-07-08 | Scene detection: PySceneDetect | Solved problem; BSD-3; deterministic; no GPU dependency; de facto standard. |
| 2026-07-08 | Vector store: LanceDB | Embedded; file-based; no server process; matches local-first constraint. |
| 2026-07-08 | Schema validation: Pydantic v2 | Runtime validation is load-bearing; JSON Schema export for non-Python consumers; widely known. |
| 2026-07-08 | Plugin system: Python entry_points | Mature; no custom loader; same mechanism as pytest and flake8; contributors already know it. |
| 2026-07-08 | Packaging: uv + hatchling | uv is the 2025–2026 community standard; meaningfully faster CI and contributor onboarding. |
| 2026-07-08 | Caching: content-addressed, keyed by (video hash + stage + model version + config hash) | Makes caching deterministic; same computation = same key; designed in from day one, not bolted on. |

---

## Deferred Ideas

These ideas are worth pursuing but are explicitly deferred until V1 is complete and stable.

| Idea | Reason for deferral |
|---|---|
| Object detection (`object_index.json`, YOLO-World) | Valuable but not blocking V1 |
| Motion classification (`motion.json`, optical flow) | Valuable but not blocking V1 |
| Cross-scene entity tracking (`relationships.json`) | Depends on V1 Scene and Event structures being stable first |
| Semantic embeddings and vector search (`semantic_index.json`) | Deferred; interface designed in V1 |
| Multi-language narration | English first; internationalization follows adoption |
| Linux/NVIDIA performance optimization | Apple Silicon is the primary development target; Linux path supported via llama.cpp interface |
| Plugin marketplace / ecosystem | The plugin interface is built in V1; an ecosystem is a V2+ growth outcome |

---

## Retired Ideas

Ideas that were considered and permanently excluded from scope.

| Idea | Reason for retirement |
|---|---|
| Conversational / chat interface ("chat with your video") | Violates the core product boundary; turns a compiler into a Video-RAG application; non-deterministic by nature; see VISION.md |
| Face recognition / biometric identity | Regulatory risk (BIPA, GDPR biometric provisions); would prevent adoption by organizations doing legal review |
| Model training or fine-tuning | Different project category; doubles maintenance surface; no product benefit for a compiler |
| Cloud service / hosted product | Violates local-first constraint; contradicts the core value proposition |
| Telemetry by default | Would be a credibility-ending discovery for the target audience |
| Opinionated importance scoring in the core | Editorial judgment belongs to consumers; not the compiler's job |
| "Moment" as a canonical term | Too vague; too marketing-flavored; excluded from GLOSSARY.md |

---

## Outstanding Risks

| Risk | Severity | Mitigation |
|---|---|---|
| PaddleOCR-VL long-term maintenance | Medium | PaddlePaddle team is active; re-evaluate at each major release; OCR is a plugin, swappable |
| mlx-vlm API stability | Medium | Tied to Apple MLX development cadence; RuntimePlugin interface absorbs changes |
| Scene grouping accuracy | High | This is custom bespoke logic; no existing library; quality entirely depends on implementation quality; requires strong golden fixtures and scoring in Phase 6 |
| Model weight availability for CI | Medium | Large model weights cannot be checked into git; CI must handle download/cache steps; golden fixtures should use small test-appropriate models |
| whisper.cpp Metal acceleration on non-M-series | Low | faster-whisper plugin handles non-Mac; documented as alternative |
| Schema stability pressure as features are added | High | Versioning discipline from day one is the only mitigation; treat any schema change as a breaking change until v1.0 is stable |

---

## Known Technical Debt

None. Implementation has not begun.

As implementation proceeds, record technical debt items here in this format:

| Module | Description | Priority | Introduced in |
|---|---|---|---|
| (none yet) | | | |
