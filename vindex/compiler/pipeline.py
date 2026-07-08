import json
import os
from pathlib import Path
from typing import Any, cast

import av

from vindex.compiler.assembler import compile_visual_memory
from vindex.compiler.event_deriver import EventDeriver
from vindex.compiler.relationship_resolver import RelationshipResolver
from vindex.compiler.scene_grouper import SceneGrouper
from vindex.compiler.scheduler import ExecutionScheduler
from vindex.core.cache import get_video_hash
from vindex.core.interfaces.runtimes import (
    ASRRuntime,
    LLMRuntime,
    MotionAnalysisRuntime,
    ObjectDetectionRuntime,
    OCRRuntime,
    SceneUnderstandingRuntime,
    SemanticEmbeddingRuntime,
)
from vindex.core.schemas.artifacts import ObservationStore, VisualMemory
from vindex.core.schemas.observations import (
    ASRWordObservation,
    CaptionObservation,
    FrameObservation,
    MotionObservation,
    ObjectObservation,
    OCRObservation,
    ShotObservation,
)
from vindex.extractors.asr.asr_extractor import ASRExtractor
from vindex.extractors.frame_extraction.pyav_extractor import PyAVFrameExtractor
from vindex.extractors.motion.motion_extractor import MotionExtractor
from vindex.extractors.objects.object_extractor import ObjectExtractor
from vindex.extractors.ocr.ocr_extractor import OCRExtractor
from vindex.extractors.scene_detection.pyscenedetect import PySceneDetectExtractor
from vindex.extractors.vlm_caption.vlm_captioner import VLMCaptioner
from vindex.narration.narrator import Narrator


def compile_video(video_path: Path, output_dir: Path, config: dict[str, Any]) -> VisualMemory:
    """Compile visual memory for a video by running extractors, compiler, and narration."""
    # 1. Check video exists
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Initialize Memory Execution Scheduler
    scheduler = ExecutionScheduler()

    # 2. Determine active stages based on config
    active_stages = config.get("stages")
    run_scene = active_stages is None or "scene" in active_stages
    run_frame = active_stages is None or "frame" in active_stages
    run_asr = active_stages is None or "asr" in active_stages
    run_ocr = active_stages is None or "ocr" in active_stages
    run_vlm = active_stages is None or "vlm" in active_stages or "caption" in active_stages
    run_object = active_stages is None or "object" in active_stages or "objects" in active_stages
    run_motion = active_stages is None or "motion" in active_stages


    # Stage 1: Scene detection (emits ShotObservations)
    shot_obs: list[ShotObservation] = []
    if run_scene:
        scene_extractor = PySceneDetectExtractor()
        shot_obs = cast(list[ShotObservation], list(scene_extractor.extract(video_path, config)))

    # Stage 2: Frame extraction
    frame_obs: list[FrameObservation] = []
    if run_frame and shot_obs:
        frame_extractor = PyAVFrameExtractor()
        frame_config = dict(config)
        frame_config["shots"] = shot_obs
        frame_config["output_dir"] = str(output_dir)
        frame_obs = cast(list[FrameObservation], list(frame_extractor.extract(video_path, frame_config)))

    # Stage 3: ASR Ingestion
    asr_obs: list[ASRWordObservation] = []
    if run_asr:
        asr_runtime = None
        asr_model_dir = None
        if "transcript_path" not in config:

            asr_key = "asr.whisper_cpp" if "binary_path" in config else "asr.faster_whisper"
            asr_model_dir = config.get("binary_path") or config.get("asr_model_dir")
            if asr_model_dir:
                asr_runtime = cast(ASRRuntime, scheduler.acquire_runtime(asr_key, Path(asr_model_dir)))
        
        asr_extractor = ASRExtractor(runtime=asr_runtime)
        asr_config = dict(config)
        if asr_model_dir:
            asr_config["model_dir"] = str(asr_model_dir)
        asr_obs = cast(list[ASRWordObservation], list(asr_extractor.extract(video_path, asr_config)))



    # Stage 4: OCR Extraction
    ocr_obs: list[OCRObservation] = []
    if run_ocr and frame_obs:
        det_model_dir = config.get("det_model_dir")
        if det_model_dir:
            ocr_runtime = cast(OCRRuntime, scheduler.acquire_runtime("ocr.paddleocr", Path(det_model_dir)))
            ocr_extractor = OCRExtractor(runtime=ocr_runtime)
            ocr_config = dict(config)
            ocr_config["frames"] = frame_obs
            ocr_obs = cast(list[OCRObservation], list(ocr_extractor.extract(video_path, ocr_config)))

    # Stage 5: VLM Captioning
    vlm_obs: list[CaptionObservation] = []
    if run_vlm and shot_obs and frame_obs:
        vlm_model_dir = config.get("vlm_model_dir")
        if vlm_model_dir:
            vlm_runtime = cast(SceneUnderstandingRuntime, scheduler.acquire_runtime("scene.mlx_vlm", Path(vlm_model_dir)))
            vlm_extractor = VLMCaptioner(runtime=vlm_runtime)
            vlm_config = dict(config)
            vlm_config["shots"] = shot_obs
            vlm_config["frames"] = frame_obs
            vlm_config["model_dir"] = str(vlm_model_dir)
            vlm_config["ocr_obs"] = ocr_obs
            vlm_obs = cast(list[CaptionObservation], list(vlm_extractor.extract(video_path, vlm_config)))

    # Stage 6: Object Extraction
    object_obs: list[ObjectObservation] = []
    if run_object and frame_obs:
        object_model_dir = config.get("object_model_dir")
        if object_model_dir:
            object_runtime = cast(ObjectDetectionRuntime, scheduler.acquire_runtime("object.yolov8", Path(object_model_dir)))
            object_extractor = ObjectExtractor(runtime=object_runtime)
            object_config = dict(config)
            object_config["frames"] = frame_obs
            object_config["model_dir"] = str(object_model_dir)
            object_obs = cast(list[ObjectObservation], list(object_extractor.extract(video_path, object_config)))


    # Stage 7: Motion Extraction
    motion_obs: list[MotionObservation] = []
    if run_motion and shot_obs and frame_obs:
        # OpenCV motion analysis uses mathematical flow computation, dummy model path acts as identifier
        motion_runtime = cast(MotionAnalysisRuntime, scheduler.acquire_runtime("motion.opencv", Path("/dummy_path")))
        motion_extractor = MotionExtractor(runtime=motion_runtime)
        motion_config = dict(config)
        motion_config["shots"] = shot_obs
        motion_config["frames"] = frame_obs
        motion_obs = cast(list[MotionObservation], list(motion_extractor.extract(video_path, motion_config)))


    # 5. Compile VisualMemory
    # Setup scene grouper with dynamic runtime selection
    embed_model_dir = config.get("embed_model_dir")
    if embed_model_dir:
        embed_runtime = cast(SemanticEmbeddingRuntime, scheduler.acquire_runtime("embed.minilm", Path(embed_model_dir)))
        scene_grouper = SceneGrouper(runtime=embed_runtime)
    else:
        # Fallback to Dummy Embedding
        from vindex.compiler.assembler import DummyEmbeddingRuntime
        scene_grouper = SceneGrouper(runtime=DummyEmbeddingRuntime())


    event_deriver = EventDeriver()

    # Get total video duration using PyAV
    container = av.open(str(video_path))
    try:
        video_stream = container.streams.video[0]
        if video_stream.duration and video_stream.time_base:
            total_duration_ms = int(float(video_stream.duration * video_stream.time_base) * 1000)
        else:
            total_duration_ms = int(container.duration / 1000.0) if container.duration else 0
    finally:
        container.close()

    video_hash = get_video_hash(video_path)

    relationship_resolver = RelationshipResolver()

    pipeline_config = dict(config)
    if embed_model_dir:
        pipeline_config["model_dir"] = str(embed_model_dir)

    visual_memory = compile_visual_memory(
        shot_obs=shot_obs,
        frame_obs=frame_obs,
        asr_obs=asr_obs,
        ocr_obs=ocr_obs,
        caption_obs=vlm_obs,
        video_hash=video_hash,
        total_duration_ms=total_duration_ms,
        scene_grouper=scene_grouper,
        event_deriver=event_deriver,
        relationship_resolver=relationship_resolver,
        config=pipeline_config,
        object_obs=object_obs,
        motion_obs=motion_obs,
    )


    # 6. Save compiled outputs to output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Save visual_memory.json
    with open(output_dir / "visual_memory.json", "w") as f:
        json.dump(visual_memory.model_dump(), f, indent=2)

    # Save timeline.json
    with open(output_dir / "timeline.json", "w") as f:
        json.dump(visual_memory.timeline.model_dump(), f, indent=2)

    # Save objects.json
    objects_list = [o.model_dump() for o in object_obs]
    with open(output_dir / "objects.json", "w") as f:
        json.dump(objects_list, f, indent=2)

    # Save motion.json
    motion_list = [m.model_dump() for m in motion_obs]
    with open(output_dir / "motion.json", "w") as f:
        json.dump(motion_list, f, indent=2)


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

    # Save observation_store.json
    from datetime import datetime, timezone
    all_observations: list[Any] = []

    all_observations.extend(shot_obs)
    all_observations.extend(frame_obs)
    all_observations.extend(asr_obs)
    all_observations.extend(ocr_obs)
    all_observations.extend(vlm_obs)
    all_observations.extend(object_obs)
    all_observations.extend(motion_obs)

    obs_store = ObservationStore(
        schema_version="2.0",
        video_hash=video_hash,
        generated_at=datetime.now(timezone.utc).isoformat(),
        observations=all_observations,
        metadata={},
    )
    with open(output_dir / "observation_store.json", "w") as f:
        json.dump(obs_store.model_dump(), f, indent=2)


    # 7. Generate grounded Markdown narration if VLM/LLM runtime is available
    if run_vlm and config.get("vlm_model_dir"):
        vlm_model_dir = config["vlm_model_dir"]
        narrator_runtime = cast(LLMRuntime, scheduler.acquire_runtime("llm.mlx_vlm", Path(vlm_model_dir)))
        narrator = Narrator(runtime=narrator_runtime)

        
        narration_config = dict(config)
        narration_config["model_dir"] = str(vlm_model_dir)
        narration_config["model_id"] = config.get("vlm_model_id", "mlx-qwen2.5-vl")
        narration_config["model_version"] = config.get("vlm_model_version", "1.0")

        md_text = narrator.narrate(visual_memory, narration_config)
        with open(output_dir / "visual_memory.md", "w") as f:
            f.write(md_text)

    # Release any active runtime from memory before returning
    scheduler.release_active()

    return visual_memory

