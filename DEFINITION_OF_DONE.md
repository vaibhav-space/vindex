# DEFINITION_OF_DONE.md — vindex

This document defines exactly what "complete" means at every level of the project. Nothing is considered done until every applicable criterion in the relevant section is satisfied. These criteria are not aspirational — they are the merge bar.

---

## Extractor Completion Criteria

An extractor is complete when all of the following are true simultaneously. Partial completion does not count.

### Interface

- [ ] Implements the canonical `Extractor` interface defined in `/core`
- [ ] Passes type checking (mypy or pyright) with no errors or suppressions
- [ ] Imports nothing from another extractor's implementation (only from `/core` schemas)

### Tests

- [ ] Unit tests cover all standard inputs (typical video, edge cases: zero shots detected, empty audio, no on-screen text)
- [ ] Unit tests cover error paths (malformed input, unsupported codec, model unavailable)
- [ ] All unit tests pass in CI
- [ ] Test coverage for the extractor module is reported in CI

### Golden Fixture

- [ ] At least one golden fixture exists in `/eval/golden/` for this extractor
- [ ] The golden fixture test is deterministic — running the extractor on the fixture input produces the fixture output byte-for-byte
- [ ] The golden fixture test is part of the CI run (not skipped, not marked xfail without documented reason)

### Schema Compliance

- [ ] All output `Observation` objects validate against their declared Pydantic schema
- [ ] `schema_version` is present in all emitted artifacts
- [ ] Validation runs as part of the extractor's standard output path (not only in tests)

### Documentation

- [ ] One documentation page exists at `/docs/extractors/<name>.md`
- [ ] The documentation page covers: what the extractor does, what inputs it accepts, what `Observation` types it emits, configuration options, and known limitations
- [ ] Public methods and classes have docstrings

### Caching

- [ ] The extractor participates in the content-addressed caching layer
- [ ] A test verifies that running the extractor twice on the same input returns the cached result on the second run

---

## Compiler Completion Criteria

The compiler is complete when:

- [ ] All five V1 extractor output streams are correctly merged into `Shot`, `Scene`, `Timeline`, and `VisualMemory` objects
- [ ] All compiler output validates against declared Pydantic schemas
- [ ] For each golden video fixture: feeding known extractor outputs produces the expected compiled output
- [ ] Unit tests cover each compiler step independently (shot assembly, scene grouping, event derivation, relationship resolution, timeline construction)
- [ ] Tests verify that the compiler is deterministic: same inputs → identical outputs across multiple runs
- [ ] `/docs/compiler.md` exists and documents the compiler's inputs, outputs, and each processing step
- [ ] CI passes with full test coverage reported

---

## Narration Layer Completion Criteria

The narration layer is complete when:

- [ ] For each golden video: the narrator produces `visual_memory.md` without errors
- [ ] A grounding test verifies that narrator output contains no claims absent from the input compiled JSON
- [ ] The narrator's output clearly labels the model and version used to generate it
- [ ] The RuntimePlugin for the narrator's LLM backend is swappable without modifying the narrator's logic
- [ ] `/docs/narration.md` documents the narration layer, its grounding requirements, and how to configure the LLM backend
- [ ] CI passes

---

## CLI and SDK Completion Criteria

The CLI and SDK layer is complete when:

- [ ] `vindex compile <video>` runs end-to-end on each golden video and produces passing artifacts
- [ ] All declared CLI flags work correctly and are covered by integration tests
- [ ] The Python SDK entry point (`from vindex import compile_video`) works and is tested
- [ ] An end-to-end integration test in CI exercises the full pipeline on a golden video
- [ ] `/docs/cli.md` and `/docs/sdk.md` are accurate and complete
- [ ] CLI `--help` output is accurate for all commands and flags

---

## Plugin System Completion Criteria

The plugin system is complete when:

- [ ] A third-party plugin can be installed in a separate package and discovered by `vindex` via `entry_points` without modifying the core package
- [ ] At least one reference plugin exists per category (ExtractorPlugin, RuntimePlugin, OutputPlugin)
- [ ] The reference plugin(s) pass their own tests in CI
- [ ] `/docs/plugins/` contains a plugin authoring guide and interface contract documentation
- [ ] All public plugin interfaces have docstrings and are exported from a stable public API path

---

## Milestone Completion Criteria

A roadmap phase is complete when:

- [ ] Every deliverable in that phase's checklist in `ROADMAP.md` is marked complete
- [ ] All tests pass in CI (unit, integration, golden fixture)
- [ ] `PROJECT_STATE.md` is updated to reflect the milestone as completed, with the completion date
- [ ] No known failing tests are skipped or marked xfail without documented justification
- [ ] The `main` branch is in a runnable state

---

## Documentation Requirements

For any public-facing feature or module:

- [ ] A documentation page exists in `/docs/`
- [ ] The documentation is accurate — it describes the current behavior, not intended future behavior
- [ ] All public API entry points (Python and CLI) are documented

For any schema change:

- [ ] `SCHEMA_VERSIONING.md` has a migration note
- [ ] All golden fixtures are updated to the new schema

---

## Performance Requirements

These are target benchmarks for the default configuration on Apple Silicon (M-series, 16GB unified memory):

| Video duration | Max acceptable compile time |
|---|---|
| 5 minutes | 3 minutes |
| 30 minutes | 20 minutes |
| 60 minutes | 45 minutes |

These targets are aspirational for V1 but must be measured. The eval harness (Phase 6) is responsible for reporting actual performance against these targets.

**Critical:** Performance must not degrade across releases. Benchmark results are committed to `/eval/results/` and compared against previous results in CI.

---

## Review Checklist

Before opening a pull request, verify:

- [ ] Tests pass locally
- [ ] Type checking passes locally
- [ ] Golden fixtures pass locally (if applicable)
- [ ] `ASSUMPTIONS.md` is updated with any undocumented decisions made during implementation
- [ ] `PROJECT_STATE.md` is updated if a milestone was completed
- [ ] `SCHEMA_VERSIONING.md` is updated if any schema was changed
- [ ] All new public APIs have docstrings
- [ ] All new documentation pages are accurate
- [ ] No network calls were introduced in non-opt-in code paths
- [ ] No new terminology was introduced without being added to `GLOSSARY.md` first
