from vindex.compiler.event_deriver import EventDeriver, jaccard_similarity
from vindex.core.schemas.artifacts import EventType, Scene, Shot
from vindex.core.schemas.observations import (
    ASRWordObservation,
    FrameObservation,
    OCRObservation,
)


def test_jaccard_similarity():
    assert jaccard_similarity("hello world", "hello world") == 1.0
    assert jaccard_similarity("hello world", "world hello") == 1.0
    assert jaccard_similarity("hello", "world") == 0.0
    assert jaccard_similarity("hello world", "hello python coder") == 0.25  # intersection "hello" (1), union "hello", "world", "python", "coder" (4)
    assert jaccard_similarity("", "") == 1.0


def test_derive_speaker_change():
    # 2 words separated by 2000ms silence
    w1 = ASRWordObservation(schema_version="1.0", timestamp_ms=100, source="asr", word="hello", start_ms=100, end_ms=500, confidence=1.0)
    w2 = ASRWordObservation(schema_version="1.0", timestamp_ms=2500, source="asr", word="world", start_ms=2500, end_ms=3000, confidence=1.0)
    
    shot = Shot(shot_id="sh001", start_ms=0, end_ms=4000, asr_words=[w1, w2])
    
    deriver = EventDeriver()
    events = deriver.derive_events([shot], [], {})
    
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == EventType.SPEAKER_CHANGE
    assert ev.start_ms == 500
    assert ev.end_ms == 2500
    assert ev.source_shot_ids == ["sh001"]


def test_derive_slide_transition():
    # 2 frames in same shot with different OCR text
    f1 = FrameObservation(schema_version="1.0", timestamp_ms=1000, source="fr", shot_id="sh001", frame_path="f1.png", frame_hash="h1")
    f2 = FrameObservation(schema_version="1.0", timestamp_ms=3000, source="fr", shot_id="sh001", frame_path="f2.png", frame_hash="h2")
    
    o1 = OCRObservation(schema_version="1.0", timestamp_ms=1000, source="ocr", text="Introduction to AI", bbox=[0,0,10,10], frame_ref="f1.png", confidence=1.0)
    o2 = OCRObservation(schema_version="1.0", timestamp_ms=3000, source="ocr", text="Deep Learning Basics", bbox=[0,0,10,10], frame_ref="f2.png", confidence=1.0)
    
    shot = Shot(shot_id="sh001", start_ms=0, end_ms=4000, frames=[f1, f2], ocr=[o1, o2])
    
    deriver = EventDeriver()
    events = deriver.derive_events([shot], [], {})
    
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == EventType.SLIDE_TRANSITION
    assert ev.start_ms == 1000
    assert ev.end_ms == 3000
    assert ev.source_shot_ids == ["sh001"]


def test_derive_scene_boundary():
    s1 = Shot(shot_id="sh001", start_ms=0, end_ms=2000)
    s2 = Shot(shot_id="sh002", start_ms=2000, end_ms=4000)
    
    sc1 = Scene(scene_id="sc001", shots=[s1], start_ms=0, end_ms=2000)
    sc2 = Scene(scene_id="sc002", shots=[s2], start_ms=2000, end_ms=4000)
    
    deriver = EventDeriver()
    events = deriver.derive_events([s1, s2], [sc1, sc2], {})
    
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == EventType.SCENE_BOUNDARY
    assert ev.start_ms == 2000
    assert ev.end_ms == 2000
    assert ev.source_shot_ids == ["sh001", "sh002"]
