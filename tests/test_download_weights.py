import subprocess
import sys
from pathlib import Path


def test_download_weights_dry_run():
    script_path = Path("scripts/download_weights.py")
    assert script_path.exists()

    result = subprocess.run(
        [sys.executable, str(script_path), "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "vindex Model Weights Setup Utility" in result.stdout
    assert "DRY RUN (no network)" in result.stdout
    assert "faster-whisper-medium" in result.stdout
    assert "all-MiniLM-L6-v2" in result.stdout
    assert "Qwen2-VL-2B-Instruct-4bit" in result.stdout


def test_download_weights_specific_model():
    script_path = Path("scripts/download_weights.py")
    result = subprocess.run(
        [sys.executable, str(script_path), "--model", "minilm", "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Selected models:    minilm" in result.stdout
    assert "all-MiniLM-L6-v2" in result.stdout
    assert "faster-whisper-medium" not in result.stdout
