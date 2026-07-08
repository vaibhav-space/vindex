from typing import Optional

from vindex.core.schemas.artifacts import Event, Relationship, Scene, Timeline


def construct_timeline(
    video_hash: str,
    scenes: list[Scene],
    events: list[Event],
    total_duration_ms: int,
    relationships: Optional[list[Relationship]] = None,
) -> Timeline:
    """Construct a Timeline object, validating all time boundaries."""
    if total_duration_ms < 0:
        raise ValueError(f"Total duration cannot be negative: {total_duration_ms}")

    # Validate scene boundaries
    for scene in scenes:
        if scene.start_ms < 0 or scene.end_ms > total_duration_ms:
            raise ValueError(
                f"Scene {scene.scene_id} time boundaries [{scene.start_ms}, {scene.end_ms}] "
                f"fall outside video duration [0, {total_duration_ms}]."
            )
        if scene.start_ms > scene.end_ms:
            raise ValueError(
                f"Scene {scene.scene_id} start time ({scene.start_ms}) "
                f"is after end time ({scene.end_ms})."
            )

    # Validate event boundaries
    for event in events:
        if event.start_ms < 0 or event.end_ms > total_duration_ms:
            raise ValueError(
                f"Event {event.event_id} time boundaries [{event.start_ms}, {event.end_ms}] "
                f"fall outside video duration [0, {total_duration_ms}]."
            )
        if event.start_ms > event.end_ms:
            raise ValueError(
                f"Event {event.event_id} start time ({event.start_ms}) "
                f"is after end time ({event.end_ms})."
            )

    # Chronologically sort scenes and events
    sorted_scenes = sorted(scenes, key=lambda s: s.start_ms)
    sorted_events = sorted(events, key=lambda e: e.start_ms)
    
    if relationships is None:
        relationships = []

    return Timeline(
        schema_version="2.0",

        video_hash=video_hash,
        scenes=sorted_scenes,
        events=sorted_events,
        relationships=relationships,
        total_duration_ms=total_duration_ms,
    )
