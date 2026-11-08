#!/usr/bin/env python3
"""
scripts/download_weights.py — Model weights download utility for vindex.

Downloads required local-first model weights to ~/.vindex/models/ (or --dest).
Supports downloading specific models and dry-run inspections.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

MODELS: Dict[str, Dict[str, Any]] = {
    "whisper": {
        "name": "faster-whisper-medium",
        "repo_id": "Systran/faster-whisper-medium",
        "folder": "faster-whisper-medium",
        "size_est": "~1.5 GB",
        "description": "Speech recognition model (multilingual, word timestamps)",
    },
    "minilm": {
        "name": "all-MiniLM-L6-v2",
        "repo_id": "sentence-transformers/all-MiniLM-L6-v2",
        "folder": "all-MiniLM-L6-v2",
        "size_est": "~90 MB",
        "description": "Text embeddings for semantic scene grouping",
    },
    "qwen": {
        "name": "Qwen2-VL-2B-Instruct-4bit",
        "repo_id": "mlx-community/Qwen2-VL-2B-Instruct-4bit",
        "folder": "Qwen2-VL-2B-Instruct-4bit",
        "size_est": "~1.3 GB",
        "description": "Visual language model for scene understanding & narration (Apple Silicon MLX)",
    },
}


def download_hf_repo(repo_id: str, local_dir: Path) -> Path:
    """Download a HuggingFace repository to a local directory."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub is required to download weights. Run: uv pip install huggingface_hub", file=sys.stderr)
        sys.exit(1)

    print(f"Downloading {repo_id} -> {local_dir}...")
    local_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
    )
    return local_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Download model weights for vindex.")
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path.home() / ".vindex" / "models",
        help="Destination directory for model weights (default: ~/.vindex/models)",
    )
    parser.add_argument(
        "--model",
        choices=["all", "whisper", "minilm", "qwen"],
        default="all",
        help="Which model to download (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned downloads and target paths without downloading bytes.",
    )

    args = parser.parse_args()
    dest_dir: Path = args.dest

    selected_keys = list(MODELS.keys()) if args.model == "all" else [args.model]

    print("==================================================")
    print("vindex Model Weights Setup Utility")
    print("==================================================")
    print(f"Target destination: {dest_dir.resolve()}")
    print(f"Selected models:    {', '.join(selected_keys)}")
    print(f"Mode:               {'DRY RUN (no network)' if args.dry_run else 'LIVE DOWNLOAD'}")
    print("==================================================")

    for key in selected_keys:
        info = MODELS[key]
        target_path = dest_dir / info["folder"]
        already_exists = target_path.exists() and any(target_path.iterdir()) if target_path.exists() else False

        print(f"\n[{key.upper()}] {info['name']} ({info['size_est']})")
        print(f"  Description: {info['description']}")
        print(f"  Repo:        {info['repo_id']}")
        print(f"  Target:      {target_path}")
        print(f"  Status:      {'Found on disk' if already_exists else 'Not found'}")

        if args.dry_run:
            continue

        if already_exists:
            print("  Skipping download because target directory already contains files.")
            continue

        download_hf_repo(info["repo_id"], target_path)
        print(f"  Completed: {target_path}")

    print("\n--------------------------------------------------")
    if args.dry_run:
        print("Dry run finished successfully. Run without --dry-run to start downloads.")
    else:
        print("Model setup complete. Set VINDEX_MODELS_DIR if using a custom directory.")
    print("--------------------------------------------------")
    return 0


if __name__ == "__main__":
    sys.exit(main())
