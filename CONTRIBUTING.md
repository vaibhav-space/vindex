# Contributing Guide

Thank you for contributing to vindex! We welcome contributions to support more models, refine compilation heuristics, and improve execution speeds.

## Code Guidelines

- **Strict Type Checking:** We enforce strict type checking using `mypy`. Ensure all function signatures and variables are fully typed.
- **Ruff Linting:** We use `ruff` for formatting and linting. Run `uv run ruff check vindex/ --fix` before committing.
- **Local-First / No Auto-Downloads:** Do not write code that automatically fetches weights from Hugging Face or other servers at runtime. All weights must be configured locally via paths (e.g. `model_dir`).
- **Tests:** Add unit tests under `tests/` for all new extractors, runtimes, and compilers.

## Creating a New Extractor

1. Inherit from `Extractor` in `vindex/core/interfaces/extractor.py`.
2. Implement `_extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[BaseObservation]`.
3. Decorate your returned observations with standard schema classes.
4. Write unit tests under `tests/extractors/test_<name>.py`.

## Creating a New Runtime

1. Define or extend a subclass of `Runtime` under `vindex/core/interfaces/runtimes.py`.
2. Implement abstract functions (e.g. `embed`, `transcribe`, `detect`).
3. Add concrete runtime classes in `vindex/runtimes/`.
4. Ensure standard imports of external heavy libraries are done inside the file, and that any missing libraries raise appropriate `ImportError` or `ModuleNotFoundError`.
