import json
from pathlib import Path

from typer.testing import CliRunner

from vindex.cli.main import app


def test_cli_compile_happy_path(tmp_path):
    runner = CliRunner()
    
    # We run compile on fixture_001 using a pre-existing transcript stub to keep it fast and model-free
    video_path = Path("eval/golden/fixture_001/video.mp4")
    output_dir = tmp_path / "dist"
    
    # Since ASR expected stub is a list of ASRWordObservation, and compile_video expects format:
    # {"words": [{"word": str, "start": float, "end": float, "confidence": float}]}
    # Let's create a valid whisper-style transcript file.
    transcript_data = {
        "words": [
            {"word": "color", "start": 0.0, "end": 1.0, "confidence": 0.99},
            {"word": "bars", "start": 1.1, "end": 2.0, "confidence": 0.98},
        ]
    }
    custom_transcript = tmp_path / "custom_transcript.json"
    with open(custom_transcript, "w") as f:
        json.dump(transcript_data, f)
        
    result = runner.invoke(
        app,
        [
            "compile",
            str(video_path),
            "-o", str(output_dir),
            "-t", str(custom_transcript),
            "--no-use-cache",  # disable caching for test run
        ]
    )
    
    assert result.exit_code == 0
    assert "Compilation successful!" in result.output
    
    # Verify outputs exist
    assert (output_dir / "visual_memory.json").exists()
    assert (output_dir / "timeline.json").exists()
    assert (output_dir / "scene_index.json").exists()
    assert (output_dir / "ocr.json").exists()
    assert (output_dir / "asr.json").exists()
    
    # Load visual_memory.json to check structure
    with open(output_dir / "visual_memory.json", "r") as f:
        vm = json.load(f)
        
    assert vm["schema_version"] == "2.0"

    assert len(vm["timeline"]["scenes"]) == 1
    assert len(vm["timeline"]["scenes"][0]["shots"]) == 1
    assert len(vm["timeline"]["scenes"][0]["shots"][0]["asr_words"]) == 2


def test_cli_compile_stages(tmp_path):
    runner = CliRunner()
    video_path = Path("eval/golden/fixture_001/video.mp4")
    output_dir = tmp_path / "dist"
    
    # Compile with only the 'scene' stage active (skips ASR, OCR, VLM)
    result = runner.invoke(
        app,
        [
            "compile",
            str(video_path),
            "-o", str(output_dir),
            "--stages", "scene",
            "--no-use-cache",
        ]
    )
    assert result.exit_code == 0
    assert "Compilation successful!" in result.output
    
    # Verify visual_memory has NO ASR words
    with open(output_dir / "visual_memory.json", "r") as f:
        vm = json.load(f)
    assert len(vm["timeline"]["scenes"][0]["shots"][0]["asr_words"]) == 0


def test_cli_compile_config(tmp_path):
    runner = CliRunner()
    video_path = Path("eval/golden/fixture_001/video.mp4")
    output_dir = tmp_path / "dist"
    
    # Write a TOML config file
    config_data = (
        "use_cache = false\n"
        "similarity_threshold = 0.85\n"
    )
    config_file = tmp_path / "config.toml"
    with open(config_file, "w") as f:
        f.write(config_data)
        
    result = runner.invoke(
        app,
        [
            "compile",
            str(video_path),
            "-o", str(output_dir),
            "-c", str(config_file),
            "--stages", "scene",
        ]
    )
    assert result.exit_code == 0
    assert "Compilation successful!" in result.output


def test_cli_inspect_and_validate(tmp_path):
    runner = CliRunner()
    
    # Create a dummy valid JSON artifact matching Pydantic Shot schema
    dummy_shot = {
        "shot_id": "sh001",
        "start_ms": 0,
        "end_ms": 1000,
        "frames": [],
        "asr_words": [],
        "ocr": [],
        "caption": None
    }
    shot_path = tmp_path / "shot.json"
    with open(shot_path, "w") as f:
        json.dump(dummy_shot, f)
        
    # Inspect
    inspect_result = runner.invoke(app, ["inspect", str(shot_path)])
    assert inspect_result.exit_code == 0
    assert '"shot_id": "sh001"' in inspect_result.output
    
    # Validate
    validate_result = runner.invoke(app, ["validate", str(shot_path), "-t", "Shot"])
    assert validate_result.exit_code == 0
    assert "Validation successful!" in validate_result.output
    
    # Validate failure case (invalid schema type)
    fail_result = runner.invoke(app, ["validate", str(shot_path), "-t", "Timeline"])
    assert fail_result.exit_code != 0
    assert "Validation failed" in fail_result.output

