import json
from pathlib import Path

from vindex.compiler.pipeline import compile_video
from vindex.core.schemas.artifacts import VisualMemory


def test_compile_video_sdk(tmp_path):
    video_path = Path("eval/golden/fixture_001/video.mp4")
    output_dir = tmp_path / "output"
    
    transcript_data = {
        "words": [
            {"word": "test", "start": 0.0, "end": 2.0, "confidence": 0.95}
        ]
    }
    transcript_file = tmp_path / "transcript.json"
    with open(transcript_file, "w") as f:
        json.dump(transcript_data, f)
        
    config = {
        "transcript_path": str(transcript_file),
        "use_cache": False,
    }
    
    vm = compile_video(video_path, output_dir, config)
    
    assert isinstance(vm, VisualMemory)
    assert vm.video_hash != ""
    assert len(vm.timeline.scenes) == 1
    assert len(vm.timeline.scenes[0].shots[0].asr_words) == 1
    assert vm.timeline.scenes[0].shots[0].asr_words[0].word == "test"
