import pytest

from vindex.compiler.timeline_constructor import construct_timeline
from vindex.core.schemas.artifacts import Event, EventType, Scene


def test_timeline_constructor_happy_path():
    scenes = [
        Scene(scene_id="sc002", shots=[], start_ms=2000, end_ms=4000),
        Scene(scene_id="sc001", shots=[], start_ms=0, end_ms=2000),
    ]
    events = [
        Event(event_id="ev001", event_type=EventType.SPEAKER_CHANGE, start_ms=500, end_ms=1000),
    ]
    
    timeline = construct_timeline("mock_hash", scenes, events, 4000)
    
    assert timeline.video_hash == "mock_hash"
    assert timeline.total_duration_ms == 4000
    # Verified chronological sorting of scenes
    assert timeline.scenes[0].scene_id == "sc001"
    assert timeline.scenes[1].scene_id == "sc002"
    assert len(timeline.events) == 1


def test_timeline_constructor_out_of_bounds():
    scenes = [
        Scene(scene_id="sc001", shots=[], start_ms=0, end_ms=5000),
    ]
    
    with pytest.raises(ValueError, match="fall outside video duration"):
        construct_timeline("mock_hash", scenes, [], 4000)


def test_timeline_constructor_negative_duration():
    with pytest.raises(ValueError, match="cannot be negative"):
        construct_timeline("mock_hash", [], [], -100)
