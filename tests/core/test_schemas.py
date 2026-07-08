
from vindex.core.schemas.artifacts import (
    ObservationStore,
    Shot,
    VisualMemory,
    migrate_v1_to_v2_visual_memory,
)
from vindex.core.schemas.observations import (
    ASRWordObservation,
    ColorObservation,
    MotionObservation,
    ObjectObservation,
)


def test_v2_observation_instantiation():
    # Verify standard metadata and lit validation
    obs = ObjectObservation(
        observation_id="obj_001",
        timestamp_ms=1000,
        duration_ms=0,
        source="yolov8",
        source_module="object_detection",
        runtime_name="ultralytics",
        runtime_version="8.0.0",
        model_name="yolov8n",
        model_version="1.0",
        processing_time_ms=12,
        confidence=0.95,
        label="person",
        bbox=[0.1, 0.2, 0.3, 0.4],
        coordinate_system="normalized"
    )
    assert obs.observation_type == "object"
    assert obs.label == "person"
    assert obs.bbox == [0.1, 0.2, 0.3, 0.4]


def test_polymorphic_observation_store():
    # Create polymorphic list with different subclass types
    objs = [
        ASRWordObservation(
            timestamp_ms=100,
            word="test",
            start_ms=100,
            end_ms=500,
            source="whisper"
        ),
        ObjectObservation(
            timestamp_ms=1000,
            label="car",
            source="yolov8"
        ),
        MotionObservation(
            timestamp_ms=2000,
            motion_score=0.85,
            camera_movement="pan",
            source="opencv"
        )
    ]
    
    store = ObservationStore(
        video_hash="dummy_hash_123",
        generated_at="2026-07-08T00:00:00Z",
        observations=objs
    )
    
    assert len(store.observations) == 3
    assert store.observations[0].observation_type == "asr"
    assert store.observations[1].observation_type == "object"
    assert store.observations[2].observation_type == "motion"
    
    # Verify serialization/deserialization loop preserves subclasses
    serialized = store.model_dump_json()
    deserialized = ObservationStore.model_validate_json(serialized)
    
    assert len(deserialized.observations) == 3
    assert isinstance(deserialized.observations[0], ASRWordObservation)
    assert isinstance(deserialized.observations[1], ObjectObservation)
    assert isinstance(deserialized.observations[2], MotionObservation)


def test_shot_v2_schema():
    # Verify Shot accepts new optional v2 objects
    shot = Shot(
        shot_id="sh001",
        start_ms=0,
        end_ms=2000,
        frames=[],
        asr_words=[],
        ocr=[],
        caption=None,
        objects=[
            ObjectObservation(timestamp_ms=500, label="chair", source="yolo")
        ],
        motion=MotionObservation(timestamp_ms=0, motion_score=0.1, camera_movement="static", source="opencv"),
        colors=ColorObservation(timestamp_ms=0, dominant_palette=["#000000"], brightness=0.5, source="color")
    )
    
    assert len(shot.objects) == 1
    assert shot.motion is not None
    assert shot.motion.camera_movement == "static"
    assert shot.colors.brightness == 0.5


def test_migration_v1_to_v2():
    # Simulates a raw v1 visual_memory.json format
    v1_data = {
        "schema_version": "1.0",
        "video_hash": "v1_video_hash",
        "generated_at": "2026-07-08T00:00:00Z",
        "timeline": {
            "schema_version": "1.0",
            "video_hash": "v1_video_hash",
            "total_duration_ms": 5000,
            "scenes": [
                {
                    "scene_id": "sc001",
                    "start_ms": 0,
                    "end_ms": 2000,
                    "shots": [
                        {
                            "shot_id": "sh001",
                            "start_ms": 0,
                            "end_ms": 2000,
                            "frames": [
                                {
                                    "timestamp_ms": 1000,
                                    "source": "frame_extraction",
                                    "shot_id": "sh001",
                                    "frame_path": "frames/sh001.png",
                                    "frame_hash": "hash"
                                }
                            ],
                            "asr_words": [],
                            "ocr": [],
                            "caption": None
                        }
                    ]
                }
            ]
        }
    }
    
    # Migrates structure
    migrated = migrate_v1_to_v2_visual_memory(v1_data)
    
    # Validates with Pydantic v2.0 VisualMemory schema
    vm = VisualMemory.model_validate(migrated)
    
    assert vm.schema_version == "2.0"
    assert vm.timeline.schema_version == "2.0"
    assert len(vm.timeline.scenes[0].shots[0].objects) == 0
    assert vm.timeline.scenes[0].shots[0].motion is None
    assert vm.timeline.scenes[0].shots[0].frames[0].observation_type == "frame"
