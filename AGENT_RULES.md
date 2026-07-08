# AGENT_RULES.md — vindex

Rules every coding agent working on this repository must follow. These rules are written in imperative voice and are non-negotiable. They exist to prevent the most common failure modes for autonomous agents on a long-lived, modular infrastructure project.

Read this file completely before writing a single line of code.

---

## Rule 1 — Schemas are law

Never change a schema file in `/core` without:

1. Bumping the `schema_version` field in that schema
2. Writing a one-line migration note in `SCHEMA_VERSIONING.md`
3. Updating all golden fixtures to match the new schema

Never emit JSON output that does not validate against its declared schema. Validation failures are load-bearing hard errors — not logged warnings to be resolved later.

---

## Rule 2 — Determinism first

Every extractor stage's output for the same input, config, and model version must be reproducible — identical byte-for-byte.

The narration layer (in `/narration`) is the one explicitly permitted exception. It must be:

- Clearly isolated in `/narration` — never mixed into `/compiler`
- Never allowed to introduce facts not present in the compiled JSON it is narrating
- Labeled in its output with the model and version used

If you are working outside `/narration` and you are about to introduce a non-deterministic operation, stop and justify it explicitly in `ASSUMPTIONS.md`.

---

## Rule 3 — No network calls unless explicitly configured

The system must run fully offline by default.

Any optional cloud or API fallback must:

- Require an explicit opt-in flag in the configuration file
- Never trigger automatically on local failure
- Never be a silent default

If you are about to add a `requests` or `httpx` call outside of an explicitly opt-in code path, stop. You are violating a non-negotiable constraint. See [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md).

---

## Rule 4 — No stage may depend on another stage's internals

An extractor may only consume another component's public `Observation` or `Event` schema output — never import from another extractor's implementation.

If this cannot be enforced by folder discipline alone, add an import-linter rule in CI.

The test: if you can delete the internals of one extractor without breaking another extractor's tests, the boundary is correct. If you cannot, the boundary is wrong.

---

## Rule 5 — Golden eval fixtures are immutable ground truth

Never delete, silently regenerate, or modify a golden fixture to make a failing test pass.

A failing test against a golden fixture means the code is wrong — not the fixture.

The only permitted exception: a human explicitly updates the fixture and commits the change with a documented reason in `SCHEMA_VERSIONING.md` (if it is a schema change) or in `/docs/adr/` (if it is a correctness correction).

---

## Rule 6 — No module merges incomplete

Every extractor or module must ship as a complete unit. A unit is complete when all of the following are true simultaneously:

- The interface is implemented and passes type checking
- Unit tests pass in CI
- At least one golden fixture exists and passes
- One documentation page exists in `/docs/`
- All outputs validate against their declared schemas

Partial implementations do not merge to `main`. A branch that merges one of these without the others has violated this rule.

See [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) for the full checklist.

---

## Rule 7 — Never hallucinate a decision — log it and keep going

If you encounter a design question not answered by `SCOPE.md`, `GLOSSARY.md`, or `ARCHITECTURE.md`:

1. Do not invent silent behavior
2. Do not stop and wait for human input
3. Write the decision and its rationale as a new entry in `ASSUMPTIONS.md`
4. Make the most conservative choice consistent with the existing rules
5. Continue

A human reviews `ASSUMPTIONS.md` later and can override anything logged there. Logging and continuing is correct behavior. Silently inventing and not logging is not.

---

## Rule 8 — Never expand scope past SCOPE.md without a documented reason

If you believe something in the "deferred" or "never" lists in `SCOPE.md` (and [VISION.md](VISION.md)) needs to move into the current phase:

1. Do not build it
2. Write the justification as a new Architecture Decision Record in `/docs/adr/`
3. Add an entry to `ASSUMPTIONS.md` flagging the decision
4. Stop — a human must review the ADR before any deferred scope is implemented

This rule exists because scope creep is the single most likely failure mode for an autonomous agent on a project with clearly defined "never" boundaries.

---

## Rule 9 — The repo must be runnable after every commit

No half-finished branches merge to `main`.

A feature branch merges only when:

- Its own tests pass in CI
- Type checking passes in CI
- The repo as a whole remains runnable

Never merge broken code with a "will fix later" comment.

---

## Rule 10 — Terminology must match GLOSSARY.md exactly

Do not introduce synonyms for terms already defined in `GLOSSARY.md`.

Prohibited examples:
- Using "Clip" to mean a metadata-only time range (it means a rendered video output)
- Using "Memory" as an internal class or module name (it is reserved for the user-facing filename `visual_memory.json`)
- Using "Moment" for any purpose (it is explicitly prohibited — see GLOSSARY.md)

If a genuinely new concept does not fit any existing term:

1. Add it to `GLOSSARY.md` as a small, standalone change
2. Open a PR or log the addition in `ASSUMPTIONS.md` before using the new term in code

---

## Rule 11 — Follow the build order; do not reorder for convenience

The build order is:

```
Phase 0 (schemas, governance files)
  → Phase 1 (extractors)
    → Phase 2 (compiler)
      → Phase 3 (narration)
        → Phase 4 (CLI and SDK)
          → Phase 5 (plugin system, documentation)
          → Phase 6 (evaluation harness)
```

Building the narration layer before the compiler exists, or building CLI polish before schemas are finalized, is always wrong regardless of how useful it appears in isolation. See [ROADMAP.md](ROADMAP.md).

---

## Rule 12 — Fail loudly and specifically when genuinely blocked

If you are genuinely blocked — not uncertain, but blocked:

- A required dependency cannot be installed
- A golden fixture cannot be produced because of a real technical barrier
- A schema constraint cannot be satisfied as currently defined

Then:

1. Stop that specific unit of work
2. Write exactly what is blocking it into `ASSUMPTIONS.md` with enough detail that a human can diagnose the issue without running the code
3. Move to the next independent unit of work
4. Do not leave a silent gap or fabricate a result

Silently skipping a requirement and marking it done is the worst possible failure mode. Loud, specific failure is always preferable.

---

## Rule 13 — Never redesign existing architecture without evidence

If you believe an existing architectural decision in [ARCHITECTURE.md](ARCHITECTURE.md) or [TECH_STACK.md](TECH_STACK.md) is wrong:

1. Do not silently redesign it
2. Write a new Architecture Decision Record in `/docs/adr/` describing the evidence for changing it and the proposed alternative
3. Log it in `ASSUMPTIONS.md`
4. Stop — a human must review before any architectural change is implemented

"I think X would be better" is not evidence. A failing test, a measured performance regression, or a documented incompatibility is evidence.

---

## Rule 14 — Update PROJECT_STATE.md after completing milestones

After completing any phase or milestone defined in [ROADMAP.md](ROADMAP.md):

1. Open [PROJECT_STATE.md](PROJECT_STATE.md)
2. Move the milestone from "In Progress" to "Completed"
3. Note the date and any deviations from the plan
4. Commit the update as part of the milestone completion PR

`PROJECT_STATE.md` is a living tracker. It is only useful if it reflects reality. Never let it drift from the actual state of the repository.

---

## Rule 15 — Never introduce hidden cloud dependencies

Beyond Rule 3 (no network calls), this rule addresses packaging:

Never add a dependency to `pyproject.toml` that:

- Makes a network call at import time
- Installs a background service or daemon
- Requires registration or account creation to function
- Sends telemetry without explicit opt-in

If you are uncertain whether a dependency does any of these things, check its source code and document your finding in `ASSUMPTIONS.md` before adding it.

---

## Rule 16 — No hidden downloads

Any model weights, datasets, or external assets must be explicitly installed by the user or configured via a local path in the config file.

The library must never initiate implicit network downloads during normal execution.

Specifically:

- Never call `model.from_pretrained("model-name")` without checking that a local `model_dir` path exists first
- If a required model path is missing, raise a clear `ModelNotFoundError` with instructions for how to download the model manually
- If a library auto-downloads on import or first use (e.g., `sentence-transformers`, `paddleocr`), suppress this with `local_files_only=True` or equivalent — and document the suppression in `ASSUMPTIONS.md`
- Use `pytest-socket` in tests to verify no network calls occur during import or execution of non-opt-in code paths

This rule directly enforces the local-first constraint in [PROJECT_CONSTRAINTS.md](PROJECT_CONSTRAINTS.md) at the code level.

---

## Summary Reference

| Rule | One-line summary |
|---|---|
| 1 | Schemas are law — bump version, write migration note |
| 2 | Determinism first — isolate narration, label non-determinism |
| 3 | No network calls without explicit opt-in config |
| 4 | No stage may import another stage's internals |
| 5 | Golden fixtures are immutable — code is wrong, not fixture |
| 6 | No module merges incomplete — all four components ship together |
| 7 | Log decisions in ASSUMPTIONS.md, make conservative choice, continue |
| 8 | No scope expansion without ADR and human review |
| 9 | Repo must be runnable after every commit |
| 10 | Terminology must match GLOSSARY.md exactly |
| 11 | Follow the build order — schemas first, always |
| 12 | Fail loudly and specifically; never silently skip |
| 13 | Never redesign architecture without evidence and ADR |
| 14 | Update PROJECT_STATE.md after completing milestones |
| 15 | Never introduce hidden cloud dependencies |
| 16 | No hidden downloads — all model paths must be explicit and local |
