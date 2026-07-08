import json
import os

from pydantic import BaseModel

from vindex.core.schemas.artifacts import (
    Event,
    ObservationStore,
    Relationship,
    Scene,
    Shot,
    Timeline,
    VisualMemory,
)
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

models: dict[str, type[BaseModel]] = {
    "ShotObservation": ShotObservation,
    "FrameObservation": FrameObservation,
    "ASRWordObservation": ASRWordObservation,
    "OCRObservation": OCRObservation,
    "CaptionObservation": CaptionObservation,
    "ObjectObservation": ObjectObservation,
    "MotionObservation": MotionObservation,
    "LayoutObservation": LayoutObservation,
    "ColorObservation": ColorObservation,
    "AudioEventObservation": AudioEventObservation,
    "Shot": Shot,
    "Scene": Scene,
    "Event": Event,
    "Relationship": Relationship,
    "Timeline": Timeline,
    "VisualMemory": VisualMemory,
    "ObservationStore": ObservationStore,
}

schema_dir = os.path.dirname(os.path.abspath(__file__))

for name, model in models.items():
    schema = model.model_json_schema()
    schema_path = os.path.join(schema_dir, f"{name}.schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Exported {name} to {schema_path}")

