from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from vindex.core.schemas.observations import (
    ASRWordObservation,
    AudioEventObservation,
    CaptionObservation,
    ColorObservation,
    FrameObservation,
    LayoutObservation,
    MotionObservation,
    ObjectObservation,
    ObservationUnion,
    OCRObservation,
)


class EventType(str, Enum):
    SPEAKER_CHANGE = "SpeakerChange"
    SLIDE_TRANSITION = "SlideTransition"
    SCENE_BOUNDARY = "SceneBoundary"
    CUSTOM = "Custom"


class Shot(BaseModel):
    """A compiled shot combining various extractor observations (v2.0)."""
    model_config = ConfigDict(frozen=True)

    shot_id: Annotated[str, Field(description="Unique identifier for this shot")]
    start_ms: Annotated[int, Field(description="Start time of this shot in milliseconds")]
    end_ms: Annotated[int, Field(description="End time of this shot in milliseconds")]
    frames: Annotated[list[FrameObservation], Field(default_factory=list, description="Keyframes sampled within this shot")]
    asr_words: Annotated[list[ASRWordObservation], Field(default_factory=list, description="ASR transcribed words falling in this shot")]
    ocr: Annotated[list[OCRObservation], Field(default_factory=list, description="OCR text detected on screen in this shot")]
    caption: Annotated[Optional[CaptionObservation], Field(default=None, description="VLM-generated caption of this shot")]
    
    # Schema v2.0 additions (defaults for backward compatibility)
    objects: Annotated[list[ObjectObservation], Field(description="Object detections inside this shot")] = []
    motion: Annotated[Optional[MotionObservation], Field(description="Motion analysis results for this shot")] = None
    layout: Annotated[Optional[LayoutObservation], Field(description="Slide/document layout parsed in this shot")] = None
    colors: Annotated[Optional[ColorObservation], Field(description="Dominant colors and brightness index")] = None
    audio_events: Annotated[list[AudioEventObservation], Field(description="Audio events occurring in this shot")] = []



class Scene(BaseModel):
    """A semantically coherent group of one or more Shots."""
    model_config = ConfigDict(frozen=True)

    scene_id: Annotated[str, Field(description="Unique identifier for this scene")]
    shots: Annotated[list[Shot], Field(description="List of shots grouped in this scene")]
    start_ms: Annotated[int, Field(description="Start time of this scene in milliseconds")]
    end_ms: Annotated[int, Field(description="End time of this scene in milliseconds")]
    dominant_caption: Annotated[Optional[str], Field(default=None, description="Summarized or representative caption for the scene")]


class Event(BaseModel):
    """A specific occurrence derived from observations."""
    model_config = ConfigDict(frozen=True)

    event_id: Annotated[str, Field(description="Unique identifier for this event")]
    event_type: Annotated[EventType, Field(description="The type of event")]
    start_ms: Annotated[int, Field(description="Start time of the event in milliseconds")]
    end_ms: Annotated[int, Field(description="End time of the event in milliseconds")]
    source_shot_ids: Annotated[list[str], Field(default_factory=list, description="List of shot IDs associated with this event")]


class Relationship(BaseModel):
    """A temporal/spatial link between two elements (e.g. OCR text overlapping a caption)."""
    model_config = ConfigDict(frozen=True)

    relationship_id: Annotated[str, Field(description="Unique identifier for this relationship")]
    source_id: Annotated[str, Field(description="ID of the source element")]
    target_id: Annotated[str, Field(description="ID of the target element")]
    relationship_type: Annotated[str, Field(description="Type of relationship (e.g., temporal_overlap, ocr_caption_match)")]
    metadata: Annotated[dict[str, Any], Field(default_factory=dict, description="Additional context metadata")]


class Timeline(BaseModel):
    """The master timeline sequencing all Scenes and Events in the video."""
    model_config = ConfigDict(frozen=True)

    schema_version: Annotated[str, Field(default="2.0", description="Schema version of this timeline")]
    video_hash: Annotated[str, Field(description="SHA-256 hash of the compiled video")]
    scenes: Annotated[list[Scene], Field(description="Chronological list of scenes")]
    events: Annotated[list[Event], Field(default_factory=list, description="Chronological list of derived events")]
    relationships: Annotated[list[Relationship], Field(default_factory=list, description="Resolved relationships between elements")]
    total_duration_ms: Annotated[int, Field(description="Total duration of the video in milliseconds")]


class VisualMemory(BaseModel):
    """The top-level compiled output index artifact."""
    model_config = ConfigDict(frozen=True)

    schema_version: Annotated[str, Field(default="2.0", description="Schema version of this visual memory")]
    video_hash: Annotated[str, Field(description="SHA-256 hash of the compiled video")]
    generated_at: Annotated[str, Field(description="ISO-8601 timestamp representing compilation completion")]
    timeline: Annotated[Timeline, Field(description="The compiled timeline")]
    metadata: Annotated[dict[str, Any], Field(default_factory=dict, description="Metadata dictionary for customization")]


# --- Observation Store Schema (v2.0) ---

class ObservationStore(BaseModel):
    """The central evidence database storing all extracted observations (v2.0)."""
    model_config = ConfigDict(frozen=True)

    schema_version: Annotated[str, Field(default="2.0", description="Schema version of the observation store")]
    video_hash: Annotated[str, Field(description="SHA-256 hash of the video")]
    generated_at: Annotated[str, Field(description="ISO-8601 timestamp representing generation completion")]
    observations: Annotated[list[ObservationUnion], Field(default_factory=list, description="Polymorphic list of normalized observations")]
    metadata: Annotated[dict[str, Any], Field(default_factory=dict, description="Metadata dictionary for customization")]


# --- Backward Compatibility Migrator Utility ---

def migrate_v1_to_v2_visual_memory(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively converts a v1.0 VisualMemory dictionary to v2.0 validation format."""
    migrated = dict(data)
    migrated["schema_version"] = "2.0"
    
    timeline = migrated.get("timeline", {})
    if not isinstance(timeline, dict):
        return migrated
        
    timeline_copy = dict(timeline)
    timeline_copy["schema_version"] = "2.0"
    
    scenes = timeline_copy.get("scenes", [])
    new_scenes = []
    for scene in scenes:
        if not isinstance(scene, dict):
            new_scenes.append(scene)
            continue
        scene_copy = dict(scene)
        shots = scene_copy.get("shots", [])
        new_shots = []
        for shot in shots:
            if not isinstance(shot, dict):
                new_shots.append(shot)
                continue
            shot_copy = dict(shot)
            # Inject new schema fields
            if "objects" not in shot_copy:
                shot_copy["objects"] = []
            if "motion" not in shot_copy:
                shot_copy["motion"] = None
            if "layout" not in shot_copy:
                shot_copy["layout"] = None
            if "colors" not in shot_copy:
                shot_copy["colors"] = None
            if "audio_events" not in shot_copy:
                shot_copy["audio_events"] = []
            
            # Map discriminator types for observations
            for frame in shot_copy.get("frames", []):
                if isinstance(frame, dict) and "observation_type" not in frame:
                    frame["observation_type"] = "frame"
            for word in shot_copy.get("asr_words", []):
                if isinstance(word, dict) and "observation_type" not in word:
                    word["observation_type"] = "asr"
            for text in shot_copy.get("ocr", []):
                if isinstance(text, dict) and "observation_type" not in text:
                    text["observation_type"] = "ocr"
            caption = shot_copy.get("caption")
            if isinstance(caption, dict) and "observation_type" not in caption:
                caption["observation_type"] = "caption"
                
            new_shots.append(shot_copy)
        scene_copy["shots"] = new_shots
        new_scenes.append(scene_copy)
    timeline_copy["scenes"] = new_scenes
    migrated["timeline"] = timeline_copy
    return migrated

