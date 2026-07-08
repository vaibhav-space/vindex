import gc
from pathlib import Path
from typing import Any, Optional

from vindex.core.interfaces.runtimes import ObjectDetectionRuntime


class YOLOv8ObjectDetectionRuntime(ObjectDetectionRuntime):
    """Object detection runtime using Ultralytics YOLOv8."""

    def __init__(self) -> None:
        self.model: Any = None
        self.loaded_model_path: Optional[Path] = None

    def load(self, model_dir_or_path: Path) -> None:
        """Load YOLO model locally into memory."""
        if self.model is not None and self.loaded_model_path == model_dir_or_path:
            return  # Already loaded

        # YOLO expects a .pt file
        if not model_dir_or_path.exists():
            raise FileNotFoundError(
                f"YOLOv8 model weights not found at: {model_dir_or_path}. "
                "Please download the weights locally. Auto-downloads are prohibited."
            )

        from ultralytics import YOLO  # type: ignore[import-not-found]

        # Initialize YOLO from local file path
        self.model = YOLO(str(model_dir_or_path))
        self.loaded_model_path = model_dir_or_path

    def unload(self) -> None:
        """Unload YOLO model to free memory."""
        self.model = None
        self.loaded_model_path = None
        gc.collect()

    def detect_objects(self, frame_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Detect objects inside an image frame."""
        model_path_str = config.get("model_path") or config.get("model_dir")
        if not model_path_str:
            raise ValueError(
                "YOLOv8ObjectDetectionRuntime requires 'model_path' (or 'model_dir') in config."
            )

        self.load(Path(model_path_str))
        if self.model is None:
            raise RuntimeError("YOLOv8 model was not loaded successfully.")

        # Run inference
        results = self.model(str(frame_path), verbose=False)
        if not results:
            return []

        result = results[0]
        detections = []
        
        # Parse boxes
        if result.boxes is not None:
            for box in result.boxes:
                # Get class label
                cls_val = box.cls[0]
                class_idx = int(cls_val.item() if hasattr(cls_val, "item") else cls_val)
                label = result.names[class_idx]
                
                # Convert xyxy [xmin, ymin, xmax, ymax] to [x, y, w, h] in pixels.
                xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy[0], "tolist") else box.xyxy[0]
                x = xyxy[0]
                y = xyxy[1]
                w = xyxy[2] - x
                h = xyxy[3] - y
                
                # Confidence score
                conf_val = box.conf[0]
                confidence = float(conf_val.item() if hasattr(conf_val, "item") else conf_val)

                
                detections.append({
                    "label": label,
                    "bbox": [x, y, w, h],
                    "confidence": confidence,
                })
                
        return detections

    @property
    def runtime_id(self) -> str:
        return "ultralytics.yolov8.v1"
