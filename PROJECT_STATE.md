# PROJECT_STATE.md — vindex

This is the living project tracker. It reflects the current state of the repository at all times. Future coding agents should be able to resume development using this file in combination with [ROADMAP.md](ROADMAP.md) and [AGENT_RULES.md](AGENT_RULES.md).

**Agents: update this file after completing any milestone. Never let it drift from reality.**

Last updated: 2026-07-08

---

## Current Status

**Phase:** Pre-implementation — Foundation (Phase 0)

**Summary:** The repository contains only documentation. No implementation code exists. The canonical documentation set has just been written and constitutes the ground-truth reference for all future implementation work.

---

## Completed Milestones

### Documentation Foundation

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

---

## In-Progress Milestones

None. Implementation has not begun.

---

## Planned Milestones

See [ROADMAP.md](ROADMAP.md) for full details. Summary:

| Phase | Description | Status |
|---|---|---|
| 0 | Foundation — repository structure, governance files, schemas, golden fixtures | Not started |
| 1 | Extractor layer — SceneDetector, FrameExtractor, ASRExtractor, OCRExtractor, VLMCaptioner, caching | Not started |
| 2 | Compiler — shot assembly, scene grouping, event derivation, timeline construction | Not started |
| 3 | Narration layer — grounded LLM Markdown generation | Not started |
| 4 | CLI and Python SDK — `vindex compile`, SDK entry points | Not started |
| 5 | Plugin system and documentation | Not started |
| 6 | Evaluation harness | Not started |

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
