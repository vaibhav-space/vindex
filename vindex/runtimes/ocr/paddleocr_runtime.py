import os
from pathlib import Path
from typing import Any, Optional

from paddleocr import PaddleOCR

from vindex.core.interfaces.runtimes import OCRRuntime


class PaddleOCRRuntime(OCRRuntime):
    """OCR runtime using PaddleOCR."""

    def __init__(self) -> None:
        self.ocr: Optional[PaddleOCR] = None
        self.loaded_det_path: Optional[Path] = None

    def load(self, model_dir_or_path: Path) -> None:
        """Load PaddleOCR models from base directory."""
        if self.ocr is not None:
            return  # Already loaded

        det_path = model_dir_or_path
        if not det_path.exists():
            raise FileNotFoundError(f"PaddleOCR detector model not found at: {det_path}")

        # Resolve rec path from det path sibling
        rec_path = det_path
        if "det" in det_path.name:
            rec_name = det_path.name.replace("det", "rec")
            candidate_rec = det_path.parent / rec_name
            if candidate_rec.exists():
                rec_path = candidate_rec

        # Hardcode default device/lang or pull from environment/config
        self.ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="en",
            det_model_dir=str(det_path),
            rec_model_dir=str(rec_path),
            device="cpu",
        )
        self.loaded_det_path = det_path

    def unload(self) -> None:
        """Unload PaddleOCR models and free memory."""
        self.ocr = None
        self.loaded_det_path = None

    def extract_text(self, frame_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract text from a frame image."""
        det_model_dir = config.get("det_model_dir")
        rec_model_dir = config.get("rec_model_dir")
        config.get("cls_model_dir")

        if not det_model_dir or not rec_model_dir:
            raise ValueError(
                "PaddleOCRRuntime requires 'det_model_dir' and 'rec_model_dir' "
                "to be configured to prevent implicit downloads."
            )

        if not os.path.exists(det_model_dir) or not os.path.exists(rec_model_dir):
            raise FileNotFoundError(
                "PaddleOCR model directories not found. Model weights must be "
                "stored locally. Auto-downloads are prohibited."
            )

        # Bypass connectivity checks
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

        # Load OCR runtime dynamically using det_model_dir
        self.load(Path(det_model_dir))

        if self.ocr is None:
            raise RuntimeError("PaddleOCR engine was not loaded successfully.")

        result = self.ocr.ocr(str(frame_path))

        if not result or result[0] is None:
            return []

        item = result[0]
        detections = []

        if isinstance(item, dict) or hasattr(item, "get"):
            # New PaddleOCR/Paddlex format (dictionary-like)
            dt_polys = item.get("dt_polys", [])
            rec_texts = item.get("rec_texts", [])
            rec_scores = item.get("rec_scores", [])
            for i in range(len(rec_texts)):
                box = dt_polys[i] if i < len(dt_polys) else []
                text = rec_texts[i]
                confidence = float(rec_scores[i]) if i < len(rec_scores) else 1.0

                # Calculate bbox as [x, y, w, h] from 4 corner points
                if len(box) >= 4:
                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    x = min(xs)
                    y = min(ys)
                    w = max(xs) - x
                    h = max(ys) - y
                else:
                    x, y, w, h = 0.0, 0.0, 0.0, 0.0

                detections.append({
                    "text": text,
                    "bbox": [float(x), float(y), float(w), float(h)],
                    "confidence": float(confidence),
                })
        else:
            # Old PaddleOCR list-of-lists format
            for line in item:
                box = line[0]  # List of 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                text, confidence = line[1]

                # Calculate bbox as [x, y, w, h] from 4 corner points
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x = min(xs)
                y = min(ys)
                w = max(xs) - x
                h = max(ys) - y

                detections.append({
                    "text": text,
                    "bbox": [float(x), float(y), float(w), float(h)],
                    "confidence": float(confidence),
                })

        return detections

    @property
    def runtime_id(self) -> str:
        return "paddleocr.v1"
