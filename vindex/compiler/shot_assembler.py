from typing import Optional

from vindex.core.schemas.artifacts import Shot
from vindex.core.schemas.observations import (
    ASRWordObservation,
    AudioEventObservation,
    CaptionObservation,
    ColorObservation,
    FrameObservation,
    LayoutObservation,
    MotionObservation,
    ObjectObservation,
    OCRObservation,
    ShotObservation,
)


def assemble_shots(
    shot_obs: list[ShotObservation],
    frame_obs: list[FrameObservation],
    asr_obs: list[ASRWordObservation],
    ocr_obs: list[OCRObservation],
    caption_obs: list[CaptionObservation],
    object_obs: Optional[list[ObjectObservation]] = None,
    motion_obs: Optional[list[MotionObservation]] = None,
    layout_obs: Optional[list[LayoutObservation]] = None,
    color_obs: Optional[list[ColorObservation]] = None,
    audio_event_obs: Optional[list[AudioEventObservation]] = None,
) -> list[Shot]:
    """Assemble individual extractor observations into structured Shot objects.
    
    All inputs and outputs are sorted chronologically by start time.
    """
    # Sort inputs chronologically
    sorted_shots = sorted(shot_obs, key=lambda x: x.start_ms)
    sorted_frames = sorted(frame_obs, key=lambda x: x.timestamp_ms)
    sorted_asr = sorted(asr_obs, key=lambda x: x.start_ms)
    sorted_ocr = sorted(ocr_obs, key=lambda x: x.timestamp_ms)
    sorted_captions = {c.shot_id: c for c in caption_obs}
    
    # Sort optional observations if provided
    sorted_objects = sorted(object_obs, key=lambda x: x.timestamp_ms) if object_obs else []
    sorted_motion = sorted(motion_obs, key=lambda x: x.timestamp_ms) if motion_obs else []
    sorted_layout = sorted(layout_obs, key=lambda x: x.timestamp_ms) if layout_obs else []
    sorted_colors = sorted(color_obs, key=lambda x: x.timestamp_ms) if color_obs else []
    sorted_audio = sorted(audio_event_obs, key=lambda x: x.timestamp_ms) if audio_event_obs else []

    assembled_shots = []

    for s_obs in sorted_shots:
        shot_id = s_obs.shot_id
        start = s_obs.start_ms
        end = s_obs.end_ms

        # Match keyframes by shot_id or timing
        shot_frames = [f for f in sorted_frames if f.shot_id == shot_id]

        # Match ASR words falling within this shot's time range
        shot_asr = [
            w for w in sorted_asr 
            if start <= w.start_ms <= end
        ]

        # Match OCR detections falling within this shot's time range
        shot_ocr = [
            o for o in sorted_ocr 
            if start <= o.timestamp_ms <= end
        ]

        # Match VLM caption
        shot_caption = sorted_captions.get(shot_id)

        # Match optional observations
        s_objects = [obj for obj in sorted_objects if start <= obj.timestamp_ms <= end]
        
        # Match motion by shot_id or fallback to timing
        s_motion = None
        for m in sorted_motion:
            if m.shot_id == shot_id:
                s_motion = m
                break
        if s_motion is None and sorted_motion:
            # Fallback to timing
            s_motion = next((m for m in sorted_motion if start <= m.timestamp_ms <= end), None)

        s_layout = next((lay for lay in sorted_layout if start <= lay.timestamp_ms <= end), None)

        s_colors = next((c for c in sorted_colors if start <= c.timestamp_ms <= end), None)
        s_audio = [a for a in sorted_audio if start <= a.timestamp_ms <= end]

        # Create structured Shot object
        assembled_shots.append(
            Shot(
                shot_id=shot_id,
                start_ms=start,
                end_ms=end,
                frames=shot_frames,
                asr_words=shot_asr,
                ocr=shot_ocr,
                caption=shot_caption,
                objects=s_objects,
                motion=s_motion,
                layout=s_layout,
                colors=s_colors,
                audio_events=s_audio,
            )
        )

    return assembled_shots

