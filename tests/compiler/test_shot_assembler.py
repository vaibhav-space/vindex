from vindex.compiler.shot_assembler import assemble_shots
from vindex.core.schemas.artifacts import Shot
from vindex.core.schemas.observations import (
    ASRWordObservation,
    CaptionObservation,
    FrameObservation,
    OCRObservation,
    ShotObservation,
)


def test_assemble_shots_happy_path():
    shot_obs = [
        ShotObservation(schema_version="1.0", timestamp_ms=0, source="sc", shot_id="sh001", start_ms=0, end_ms=2000),
        ShotObservation(schema_version="1.0", timestamp_ms=2000, source="sc", shot_id="sh002", start_ms=2000, end_ms=4000),
    ]
    frame_obs = [
        FrameObservation(schema_version="1.0", timestamp_ms=1000, source="fr", shot_id="sh001", frame_path="1.png", frame_hash="h1"),
        FrameObservation(schema_version="1.0", timestamp_ms=3000, source="fr", shot_id="sh002", frame_path="2.png", frame_hash="h2"),
    ]
    asr_obs = [
        ASRWordObservation(schema_version="1.0", timestamp_ms=500, source="asr", word="hello", start_ms=500, end_ms=900, confidence=0.9),
        ASRWordObservation(schema_version="1.0", timestamp_ms=2500, source="asr", word="world", start_ms=2500, end_ms=2900, confidence=0.95),
    ]
    ocr_obs = [
        OCRObservation(schema_version="1.0", timestamp_ms=1000, source="ocr", text="Slide", bbox=[0,0,10,10], frame_ref="1.png", confidence=0.9),
    ]
    caption_obs = [
        CaptionObservation(schema_version="1.0", timestamp_ms=0, source="vlm", shot_id="sh001", caption_text="First shot", model_id="m1", model_version="v1"),
    ]
    
    shots = assemble_shots(shot_obs, frame_obs, asr_obs, ocr_obs, caption_obs)
    
    assert len(shots) == 2
    
    s1 = shots[0]
    assert isinstance(s1, Shot)
    assert s1.shot_id == "sh001"
    assert s1.start_ms == 0
    assert s1.end_ms == 2000
    assert len(s1.frames) == 1
    assert s1.frames[0].frame_path == "1.png"
    assert len(s1.asr_words) == 1
    assert s1.asr_words[0].word == "hello"
    assert len(s1.ocr) == 1
    assert s1.ocr[0].text == "Slide"
    assert s1.caption is not None
    assert s1.caption.caption_text == "First shot"
    
    s2 = shots[1]
    assert s2.shot_id == "sh002"
    assert len(s2.frames) == 1
    assert len(s2.asr_words) == 1
    assert s2.asr_words[0].word == "world"
    assert len(s2.ocr) == 0
    assert s2.caption is None


def test_assemble_shots_empty():
    assert assemble_shots([], [], [], [], []) == []
