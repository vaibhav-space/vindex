import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from vindex.compiler.event_deriver import EventDeriver
from vindex.compiler.relationship_resolver import RelationshipResolver
from vindex.compiler.scene_grouper import SceneGrouper
from vindex.compiler.shot_assembler import assemble_shots
from vindex.compiler.timeline_constructor import construct_timeline
from vindex.core.interfaces.runtimes import SemanticEmbeddingRuntime
from vindex.core.schemas.artifacts import VisualMemory

# ... existing schema imports ...
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


class DummyEmbeddingRuntime(SemanticEmbeddingRuntime):
    """Fallback embedding runtime that returns dummy zero vectors."""

    def load(self, model_dir_or_path: Path) -> None:
        pass

    def unload(self) -> None:
        pass

    def embed_text(self, texts: list[str], config: dict[str, Any]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]

    @property
    def runtime_id(self) -> str:
        return "dummy_embed"



def compile_visual_memory(
    shot_obs: list[ShotObservation],
    frame_obs: list[FrameObservation],
    asr_obs: list[ASRWordObservation],
    ocr_obs: list[OCRObservation],
    caption_obs: list[CaptionObservation],
    video_hash: str,
    total_duration_ms: int,
    scene_grouper: SceneGrouper,
    event_deriver: EventDeriver,
    relationship_resolver: Optional[RelationshipResolver] = None,
    config: Optional[dict[str, Any]] = None,
    object_obs: Optional[list[ObjectObservation]] = None,
    motion_obs: Optional[list[MotionObservation]] = None,
    layout_obs: Optional[list[LayoutObservation]] = None,
    color_obs: Optional[list[ColorObservation]] = None,
    audio_event_obs: Optional[list[AudioEventObservation]] = None,
) -> VisualMemory:
    """Compile raw observation streams into the final VisualMemory artifact."""
    if config is None:
        config = {}

    # 1. Assemble Shots
    shots = assemble_shots(
        shot_obs,
        frame_obs,
        asr_obs,
        ocr_obs,
        caption_obs,
        object_obs=object_obs,
        motion_obs=motion_obs,
        layout_obs=layout_obs,
        color_obs=color_obs,
        audio_event_obs=audio_event_obs,
    )


    # 2. Group into Scenes
    scenes = scene_grouper.group_scenes(shots, config)

    # 3. Derive Events
    events = event_deriver.derive_events(shots, scenes, config)

    # 3.5 Resolve Relationships
    if relationship_resolver is None:
        relationship_resolver = RelationshipResolver()
    relationships = relationship_resolver.resolve_relationships(shots, config)

    # 4. Construct Timeline
    timeline = construct_timeline(video_hash, scenes, events, total_duration_ms, relationships)

    # 5. Assemble VisualMemory
    generated_at = datetime.now(timezone.utc).isoformat()
    return VisualMemory(
        schema_version="2.0",

        video_hash=video_hash,
        generated_at=generated_at,
        timeline=timeline,
        metadata={},
    )


def compile_from_observations(
    fixture_dir: Path,
    output_dir: Path,
    scene_grouper: Optional[SceneGrouper] = None,
) -> dict[str, Any]:
    """Compile observations stored in a golden fixture directory and write to output_dir."""
    # 1. Read metadata.json
    metadata_path = fixture_dir / "metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    duration_ms = int(metadata["duration_ms"])

    # 2. Load observations from fixture stubs
    expected_dir = fixture_dir / "expected"
    
    # Load ASR
    asr_path = expected_dir / "asr.json"
    with open(asr_path, "r") as f:
        asr_raw = json.load(f)
    asr_obs = [ASRWordObservation.model_validate(w) for w in asr_raw]

    # Load OCR
    ocr_path = expected_dir / "ocr.json"
    with open(ocr_path, "r") as f:
        ocr_raw = json.load(f)
    ocr_obs = [OCRObservation.model_validate(o) for o in ocr_raw]

    # Load timeline/shot stubs to extract shots, frames, captions
    timeline_path = expected_dir / "timeline.json"
    with open(timeline_path, "r") as f:
        timeline_raw = json.load(f)
    
    shot_obs = []
    frame_obs = []
    caption_obs = []
    video_hash = str(timeline_raw.get("video_hash", "fixture_hash"))

    for scene in timeline_raw.get("scenes", []):
        for shot in scene.get("shots", []):
            shot_id = shot["shot_id"]
            start_ms = shot["start_ms"]
            end_ms = shot["end_ms"]
            
            shot_obs.append(
                ShotObservation(
                    schema_version="1.0",
                    timestamp_ms=start_ms,
                    source="scene_detection.pyscenedetect.v1",
                    shot_id=shot_id,
                    start_ms=start_ms,
                    end_ms=end_ms,
                )
            )

            for frame in shot.get("frames", []):
                frame_obs.append(FrameObservation.model_validate(frame))

            caption = shot.get("caption")
            if caption:
                caption_obs.append(CaptionObservation.model_validate(caption))

    # 3. Setup defaults for compilers if not provided
    if scene_grouper is None:
        dummy_runtime = DummyEmbeddingRuntime()
        scene_grouper = SceneGrouper(runtime=dummy_runtime)
    
    event_deriver = EventDeriver()

    # 4. Compile
    visual_memory = compile_visual_memory(
        shot_obs=shot_obs,
        frame_obs=frame_obs,
        asr_obs=asr_obs,
        ocr_obs=ocr_obs,
        caption_obs=caption_obs,
        video_hash=video_hash,
        total_duration_ms=duration_ms,
        scene_grouper=scene_grouper,
        event_deriver=event_deriver,
    )

    # 5. Write secondary output files to output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Save visual_memory.json
    with open(output_dir / "visual_memory.json", "w") as f:
        json.dump(visual_memory.model_dump(), f, indent=2)

    # Save timeline.json
    with open(output_dir / "timeline.json", "w") as f:
        json.dump(visual_memory.timeline.model_dump(), f, indent=2)

    # Save scene_index.json
    scenes_list = [s.model_dump() for s in visual_memory.timeline.scenes]
    with open(output_dir / "scene_index.json", "w") as f:
        json.dump(scenes_list, f, indent=2)

    # Save ocr.json
    ocr_list = [o.model_dump() for o in ocr_obs]
    with open(output_dir / "ocr.json", "w") as f:
        json.dump(ocr_list, f, indent=2)

    # Save asr.json
    asr_list = [a.model_dump() for a in asr_obs]
    with open(output_dir / "asr.json", "w") as f:
        json.dump(asr_list, f, indent=2)

    return visual_memory.model_dump()
