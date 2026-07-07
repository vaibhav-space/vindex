# VISION.md — vindex

## Mission

> Compile any video, once, into a deterministic, inspectable, versioned knowledge artifact — so no AI system ever has to watch the same video twice.

---

## The Gap This Project Closes

Video is the one major data modality with no durable, open, local-first compilation layer.

- **Text** has had this for decades. Parsers, indexers, and embedding pipelines are boring, solved infrastructure.
- **Documents** got it recently. Tesseract, then a wave of document-AI tools, created a stable layer between scanned pages and downstream systems.
- **Video** has not. Every system that touches video still re-derives understanding from raw pixels, every time, non-reproducibly, usually behind a cloud API meter.

`vindex` exists to close that gap permanently — as infrastructure rather than as a product feature of any one application.

---

## First Principles

**Video understanding is not one problem.**

It is a bundle of independently solvable problems — where are the cuts, what is on screen, what is said, what is written, what moved — wearing a trenchcoat. Each problem should be treated as a separate, independently verifiable claim about the world. A model that solves all of them in a single forward pass is not simpler; it is un-auditable.

**Determinism is a first-class requirement, not an aspiration.**

Same video, same config, same model version → byte-identical output. This is what makes caching, testing, diffing, and trust possible. The one deliberately non-deterministic stage — LLM narration — must be architecturally isolated and clearly labeled. It must never mix silently into the deterministic layers.

**The compiler produces facts; it never produces opinions.**

"The caption overlaps the graph" is a fact — a geometric and temporal relationship, computably verifiable. "This is the most important moment in the video" is an editorial judgment. The compiler surfaces what a video contains. Every decision about which facts matter belongs to the consumer.

**Modularity is enforced by interface, not convention.**

A contributor adding a new extractor must never need to read or modify the compiler, the narrator, or another extractor. If achieving that requires more upfront interface design, that cost is worth paying once, permanently, rather than accumulating coupling debt forever.

**Extensibility means swap without forking.**

Every replaceable component — the VLM, the OCR engine, the embedding model — sits behind an interface a plugin can implement. The measure of success is not "does the default pipeline work well." It is "can someone replace exactly one piece without touching anything else."

**Reproducibility extends to the artifact schema itself.**

Someone will build a dataset, a search index, or a product on top of `visual_memory.json`. Schema changes carry the same discipline as database schema migrations: explicit versioning, documented migration paths, no silent breaking changes.

**Developer experience is a correctness property.**

A pipeline this modular lives or dies on whether a new contributor can understand where their piece fits without reading the whole system. Typed interfaces, clear folder boundaries, and a glossary that is enforced — not just documented — are what keep a genuinely modular architecture from decaying into a tangled one after twenty contributors have touched it.

---

## Engineering Philosophy

`vindex` is infrastructure. The right comparison is not to AI tools or video products. The right comparison is to compilers, indexers, and parsing libraries.

Infrastructure projects that become durable (ffmpeg, Tesseract, SQLite, Whisper) share one trait: they resisted scope creep into being an "experience" and stayed a dependable layer. The single biggest threat to this project is growing a chat interface or an editorial judgment layer into its core — because that demo well, and that is exactly what turns infrastructure into an app with a shelf life.

This project succeeds if, five years from now, it is the boring, unglamorous, widely-depended-upon layer that a dozen unrelated tools — editors, research pipelines, agents, search engines, accessibility tools — all quietly sit on top of, the way many unrelated tools today quietly sit on top of ffmpeg or Whisper without anyone thinking of it as remarkable.

---

## Positioning

**Primary:** `vindex` is the open-source compiler for video understanding.

**One-line analogy:** Think Tesseract, but for everything a video contains — not just the text in it.

**What it is not:** A chatbot. A summarizer. A highlight picker. A video QA system. A cloud API. A model training framework.

---

## Scope

### Belongs in V1 — the deterministic core

- Shot and scene boundary detection
- Deterministic keyframe sampling per shot
- Vision-language captioning per keyframe and shot
- OCR extraction of on-screen text (captions, slides, UI, lower-thirds)
- ASR ingestion — accept an existing transcript with word-level timestamps as an input contract, and also run local ASR when none is supplied
- Deterministic compiler that merges the above into `scene_index`, `timeline`, `ocr`, and `visual_memory` artifacts
- A Markdown narration layer that phrases (never invents) the compiled facts
- Python SDK and CLI
- Versioned JSON schemas for every output artifact, from day one
- Content-addressed local cache keyed by `(video hash, pipeline stage, model version, config hash)`

### Deferred — real, valuable, but not blocking a useful V1

- Open-vocabulary object detection and `object_index.json`
- Motion and camera-movement classification (`motion.json`)
- Cross-scene entity tracking and `relationships.json`
- Semantic embeddings and vector search (`semantic_index.json`)
- A plugin ecosystem — the plugin interface belongs in V1; the ecosystem is a V2+ growth outcome
- Multi-language narration output
- Non-Apple-Silicon performance optimization (support the interface; defer the tuning)

### Never — draw this line hard, in writing, before any code exists

- **No chat or QA interface.** The SDK compiles facts; it does not answer user questions in a conversational loop. The moment this project grows a "chat with your video" feature, it has quietly become a Video-RAG application — a different product — and inherits all the non-determinism and re-derivation problems it exists to eliminate.
- **No face recognition or biometric identity.** Beyond the technical reasons, biometric identification is a different regulatory category (BIPA, GDPR biometric provisions) that would prevent adoption by any organization doing legal review.
- **No model training or fine-tuning.** The SDK orchestrates existing models. It is not an ML training project. Mixing these doubles the maintenance surface for no product benefit.
- **No hosted service, no telemetry-by-default, no silent network calls.** A single silent network call in v1 would be a credibility-ending discovery for the exact audience — privacy-conscious engineers, offline production houses, compliance-sensitive companies — most likely to adopt it.
- **No opinionated importance scoring or highlight detection in the core.** That is an editorial judgment that belongs to consumers. The compiler's job is facts.

---

## Non-Goals

- `vindex` is not a video player, editor, or rendering tool.
- `vindex` is not a benchmarking framework for video QA tasks.
- `vindex` is not a cloud service or SaaS product.
- `vindex` is not an agent memory system. The output is a compiled index — static, re-derivable from source, immutable by design. It does not decay, merge, or forget. It is not Mem0, Zep, or Letta.
- `vindex` does not define what downstream consumers should do with compiled knowledge. That is deliberately out of scope.

---

## Why This Project Should Exist

The compiler category for video is empty. Text has parsers and indexers. Documents have Tesseract and layout models. Audio has Whisper. Video has cloud APIs and one-off scripts.

Anyone building a video-aware AI product today has three options: pay a cloud API per minute, build the extraction pipeline themselves, or skip the extraction and re-derive from raw video every time. All three options are expensive, brittle, or both.

`vindex` offers a fourth option: compile once, reuse forever, entirely on local infrastructure. That option does not currently exist as maintained, open, versioned infrastructure. That is why this project should exist.
