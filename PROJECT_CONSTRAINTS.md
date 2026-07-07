# PROJECT_CONSTRAINTS.md — vindex

These constraints are non-negotiable. They are not design preferences or default behaviors. They are the properties that define what `vindex` is. Violating any of them changes what the project fundamentally is.

Any proposal to weaken or remove a constraint requires an Architecture Decision Record in `/docs/adr/` and explicit maintainer approval. No agent may weaken these constraints unilaterally.

---

## 1. Local-first by default

The system must run fully offline without any configuration change.

- No network calls may occur during a default `vindex compile` run
- No API keys, registration, or cloud accounts are required to use the SDK
- Optional cloud or API integrations require an explicit opt-in flag in the user's config file
- No automatic fallback to a remote endpoint when a local operation fails

**Why this is non-negotiable:** The audience most likely to adopt `vindex` — privacy-conscious engineers, offline production environments, compliance-sensitive organizations — cannot use a tool that makes undisclosed network calls. A single silent network call discovered in production would permanently damage trust with this audience.

---

## 2. Deterministic output

For the same video file, the same configuration, and the same model versions, the pipeline must produce byte-identical output.

- All extractor stages must be deterministic
- Caching must rely on determinism — if output were non-deterministic, cached results would be silently wrong
- The narration layer is the one explicitly permitted exception, and it must be clearly isolated in `/narration` and labeled in its output

**Why this is non-negotiable:** Determinism is what makes the output trustworthy as an artifact. It enables caching, diffing, testing against golden fixtures, and citing in research. Non-deterministic output cannot be versioned, cannot be cached reliably, and cannot be cited reproducibly.

---

## 3. Plugin-based extensibility

Every major component — OCR engine, VLM backend, ASR engine, model runtime — must be replaceable via a plugin interface without forking the core package.

- Extractor plugins implement the `Extractor` interface
- Runtime plugins implement the `RuntimePlugin` interface
- Plugin discovery uses Python `entry_points` — no custom loader
- No extractor may be hardcoded into the compiler or CLI in a way that requires code changes to swap

**Why this is non-negotiable:** The default pipeline will not suit every use case. Users with different hardware, different model preferences, or different quality requirements must be able to replace components without maintaining a fork. A project that cannot be customized without forking will be forked — and fragmented.

---

## 4. Versioned output schemas

Every output artifact must carry a `schema_version` field. Schema changes are never silent.

- All output JSON validates against a versioned Pydantic schema
- Breaking schema changes require a version bump and a migration note in `SCHEMA_VERSIONING.md`
- Additive schema changes (new optional fields) require a minor version bump
- Removing or renaming schema fields requires a major version bump and a documented migration path

**Why this is non-negotiable:** Users will build downstream systems — search indexes, datasets, products — on top of `visual_memory.json`. A schema that changes shape silently breaks every downstream consumer without warning. The discipline here is the same as database schema migrations: version everything, migrate explicitly.

---

## 5. Reproducibility

The output of the pipeline is a stable, re-derivable artifact. It is not mutable state.

- Running `vindex compile` on the same video at any point in time must be capable of producing the same artifact (given the same config and model versions)
- The artifact does not decay, merge, or expire
- The artifact does not track user state or session history
- The caching layer must not serve stale results when model version or config changes

**Why this is non-negotiable:** `vindex` is positioned as a compiler, not as an agent memory system. An artifact that changes over time, decays, or depends on prior runs is not a compiled artifact — it is a stateful system. That is a different product with different properties and different trust guarantees.

---

## 6. Open-source friendly

All default dependencies must be open-source with licenses compatible with the MIT license of this project.

- Preferred licenses: MIT, Apache 2.0, BSD-2, BSD-3
- GPL dependencies: only permissible if they are optional plugins, never in the core package
- Proprietary model weights: never required by default; only permissible as explicitly opt-in plugins

**Why this is non-negotiable:** The project's credibility as infrastructure depends on any organization being able to audit, modify, and deploy it without license review complications. A GPL dependency in the core package would prevent adoption by any organization with standard IP policies.

---

## 7. Stable public APIs

Public interfaces — the Python SDK entry points, the CLI command surface, the Extractor interface, the RuntimePlugin interface, the output artifact schemas — are stable once released.

- Breaking changes to public APIs require a major version bump and a documented migration guide
- Deprecation warnings must precede removal by at least one minor release
- Internal APIs (anything in `/compiler` internals, `/narration` internals) may change freely

**Why this is non-negotiable:** Downstream consumers depend on the stability of the public surface. A project that breaks its API in minor releases is not infrastructure — it is a prototype.

---

## 8. No vendor lock-in

No output artifact, schema, or internal representation may use a proprietary format or require a proprietary tool to read.

- All output is plain JSON and Markdown
- All schemas are standard JSON Schema, exportable from Pydantic
- The caching layer uses a standard file-based format
- Vector indexes use LanceDB's open format

**Why this is non-negotiable:** Lock-in defeats the "your index is yours" value proposition. If reading `visual_memory.json` requires a specific proprietary tool or service, the output is not portable — it is just a different form of cloud lock-in.

---

## 9. No chat interface, no QA interface, no editorial judgment in the core

The compiler does not answer questions about videos. It does not score importance. It does not surface highlights. It does not generate summaries in response to user questions.

These are legitimate products. They are not this one.

**Why this is non-negotiable:** The moment `vindex` grows a conversational or editorial layer into its core, it becomes a Video-RAG application — a different product that inherits all the non-determinism, re-derivation costs, and subjective judgment problems that `vindex` exists to eliminate. This boundary, once crossed, cannot be uncrossed without a full rewrite. It must be enforced in writing before any code exists.

---

## 10. Prefer mature dependencies

Before building any capability from scratch, verify that no mature open-source library already solves the problem correctly.

- A "mature" dependency has: active maintenance, a stable API, meaningful community adoption, and a compatible license
- When a mature library exists, use it — reinventing solved problems buys nothing and creates maintenance burden
- When no mature library exists (e.g., scene grouping logic), document why in the relevant section of [TECH_STACK.md](TECH_STACK.md)

**Why this is non-negotiable:** The project's long-term maintenance load must remain manageable. Every line of custom code that replaces a mature library is a line that must be maintained, tested, and debugged in perpetuity.
