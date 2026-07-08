from typing import Any

from vindex.core.schemas.artifacts import Event, EventType, Scene, Shot
from vindex.core.schemas.observations import ASRWordObservation


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate the Jaccard word similarity between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 and not words2:
        return 1.0
    union = words1.union(words2)
    intersection = words1.intersection(words2)
    return len(intersection) / len(union)


class EventDeriver:
    """Derives semantic Events from compiled Shots and Scenes."""

    def derive_events(self, shots: list[Shot], scenes: list[Scene], config: dict[str, Any]) -> list[Event]:
        """Orchestrate event derivation from patterns in shots and scenes."""
        events: list[Event] = []
        event_counter = 1

        # 1. Derive SpeakerChange events from ASR gaps (> 1500ms silence)
        # Gather all ASR words across all shots and sort chronologically
        all_asr: list[ASRWordObservation] = []
        for shot in shots:
            all_asr.extend(shot.asr_words)
        all_asr = sorted(all_asr, key=lambda w: w.start_ms)

        silence_threshold_ms = config.get("speaker_change_silence_ms", 1500)
        for i in range(1, len(all_asr)):
            prev_word = all_asr[i - 1]
            curr_word = all_asr[i]
            gap = curr_word.start_ms - prev_word.end_ms
            if gap > silence_threshold_ms:
                # Find which shots contain these words to reference them
                source_shots = []
                for shot in shots:
                    if shot.start_ms <= prev_word.end_ms <= shot.end_ms:
                        source_shots.append(shot.shot_id)
                    if shot.start_ms <= curr_word.start_ms <= shot.end_ms:
                        if shot.shot_id not in source_shots:
                            source_shots.append(shot.shot_id)

                events.append(
                    Event(
                        event_id=f"ev{event_counter:03d}",
                        event_type=EventType.SPEAKER_CHANGE,
                        start_ms=prev_word.end_ms,
                        end_ms=curr_word.start_ms,
                        source_shot_ids=source_shots,
                    )
                )
                event_counter += 1

        # 2. Derive SlideTransition events from OCR transitions
        # Compare consecutive keyframes within the same shot
        for shot in shots:
            if len(shot.frames) > 1:
                # Gather OCR observations attached to the frames of this shot
                # We sort frames by timestamp
                sorted_frames = sorted(shot.frames, key=lambda f: f.timestamp_ms)
                for i in range(1, len(sorted_frames)):
                    f1 = sorted_frames[i - 1]
                    f2 = sorted_frames[i]

                    # Gather OCR text for f1 and f2
                    t1 = " ".join([o.text for o in shot.ocr if o.frame_ref == f1.frame_path])
                    t2 = " ".join([o.text for o in shot.ocr if o.frame_ref == f2.frame_path])

                    # If text exists on either, and Jaccard similarity is low, we have a transition
                    if (t1 or t2) and jaccard_similarity(t1, t2) < 0.5:
                        events.append(
                            Event(
                                event_id=f"ev{event_counter:03d}",
                                event_type=EventType.SLIDE_TRANSITION,
                                start_ms=f1.timestamp_ms,
                                end_ms=f2.timestamp_ms,
                                source_shot_ids=[shot.shot_id],
                            )
                        )
                        event_counter += 1

        # 3. Derive SceneBoundary events from adjacent Scenes
        sorted_scenes = sorted(scenes, key=lambda s: s.start_ms)
        for i in range(1, len(sorted_scenes)):
            s1 = sorted_scenes[i - 1]
            s2 = sorted_scenes[i]
            
            # Find the shot IDs involved on the boundary
            source_shots = []
            if s1.shots:
                source_shots.append(s1.shots[-1].shot_id)
            if s2.shots:
                source_shots.append(s2.shots[0].shot_id)

            events.append(
                Event(
                    event_id=f"ev{event_counter:03d}",
                    event_type=EventType.SCENE_BOUNDARY,
                    start_ms=s1.end_ms,
                    end_ms=s2.start_ms,
                    source_shot_ids=source_shots,
                )
            )
            event_counter += 1

        # Return all derived events sorted chronologically by start time
        return sorted(events, key=lambda e: e.start_ms)
