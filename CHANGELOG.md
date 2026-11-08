# Changelog

All notable changes to the `vindex` (distribution `vindex-video`) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] — 2026-11-08

### Added
- **Model Weights Setup Script (`scripts/download_weights.py`)**:
  - Download utility supporting faster-whisper, sentence-transformers, and Qwen2-VL local weights.
  - Added `--dry-run` flag to inspect planned downloads and local paths without touching the network.
  - Added unit test suite `tests/test_download_weights.py`.
- **Web Studio Live Video Preview**:
  - Added embedded video preview player in `vindex/api/static/index.html` displaying video playback, resolution, and duration immediately upon file selection.
- **GitHub Actions Test Automation**:
  - Added automated `test` workflow in `.github/workflows/ci.yml` running unit and integration tests with `ffmpeg` on Ubuntu runners.
- **Interactive Developer Landing Page**:
  - Overhauled `website/` with an interactive artifact explorer displaying actual golden fixture outputs (`visual_memory.json`, `visual_memory.md`, `timeline.json`, `asr.json`, `ocr.json`).
  - Added 4-stage pipeline architectural diagram and multi-tab developer interface examples (SDK, CLI, REST API, Plugin System).

### Changed
- **Machine-Independent Path Portability**:
  - Replaced hardcoded machine-specific paths in `vindex/api/app.py` and `tests/test_e2e_heavy.py` with environment variable configuration (`VINDEX_MODELS_DIR`, `VINDEX_JOBS_DIR`, `VINDEX_ASR_MODEL_DIR`, etc.) and sensible user-home fallbacks (`~/.vindex/`).
  - Corrected relative links in `docs/contributing.md`.
- **Packaging & PyPI Distribution**:
  - Updated distribution name to `vindex-video` in `pyproject.toml` to avoid collision with an unrelated package on PyPI, while retaining the standard `vindex` Python import namespace.
  - Documented reproducible source installation workflow (`uv sync` or `pip install -e .`).
- **Static Analysis & Type Checking**:
  - Resolved unused `type: ignore` comments in `vindex/runtimes/vision/mlx_vlm_runtime.py`, achieving 100% clean `mypy` strict type checking across all 49 source files.
- **Documentation Synchronization**:
  - Updated `docs/PROJECT_STATE.md` and `docs/ROADMAP.md` to accurately reflect completed implementation of CLI commands (`inspect`, `validate`, `--stages`), compiler `RelationshipResolver`, and plugin dynamic discovery.
  - Updated `README.md` with correct repository links (`vaibhav-space/vindex`) and accurate model configuration guides.

---

## [0.1.0] — 2026-07-08

### Added
- Initial open-source release of the local-first video knowledge compiler.
- Extractor plugins for Scene Detection, PyAV keyframes, faster-whisper ASR, PaddleOCR, and Qwen2-VL captioning.
- Deterministic compiler and timeline constructor.
- Strictly grounded LLM Markdown narration layer.
- Typer CLI (`vindex compile`, `vindex eval`).
- FastAPI REST service with basic Web Studio UI.
- Golden fixture evaluation harness.
