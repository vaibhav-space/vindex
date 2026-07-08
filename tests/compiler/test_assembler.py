from pathlib import Path

from vindex.compiler.assembler import compile_from_observations


def test_compile_from_observations_fixture_001(tmp_path):
    fixture_dir = Path("eval/golden/fixture_001")
    output_dir = tmp_path / "output"
    
    result = compile_from_observations(fixture_dir, output_dir)
    
    assert isinstance(result, dict)
    assert result["schema_version"] == "2.0"

    assert result["video_hash"] == "mock_hash_fixture_001"
    assert "generated_at" in result
    assert "timeline" in result
    
    # Verify outputs are written on disk
    assert (output_dir / "visual_memory.json").exists()
    assert (output_dir / "timeline.json").exists()
    assert (output_dir / "scene_index.json").exists()
    assert (output_dir / "ocr.json").exists()
    assert (output_dir / "asr.json").exists()
