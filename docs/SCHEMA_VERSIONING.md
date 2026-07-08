# SCHEMA_VERSIONING.md — vindex

This file documents the rules for versioning and migrating output schemas in vindex. It also serves as the migration log.

## Versioning Rules

- Every artifact schema must carry a `schema_version` field in the format `MAJOR.MINOR` (e.g. `"1.0"`).
- All JSON artifacts output by vindex must validate against their declared schema.
- **Additive changes** (e.g. adding a new optional field with a default value) require a **minor version bump** (e.g. `1.0` to `1.1`).
- **Breaking changes** (e.g. removing a field, renaming a field, changing a field type, or making an optional field required) require a **major version bump** (e.g. `1.0` to `2.0`).
- Every schema change must be documented in the **Migration Log** below before merging.
- If a schema version is bumped, all golden fixtures must be updated to match the new schema structure immediately in the same commit.

## Migration Log

| Date | Schema | From | To | Description |
|---|---|---|---|---|
| 2026-07-08 | All schemas | — | 1.0 | Initial version of vindex schemas defined in Phase 0. |
