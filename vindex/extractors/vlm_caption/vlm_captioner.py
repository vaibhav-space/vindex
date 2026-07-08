from pathlib import Path
from typing import Any, Iterator, Optional

from vindex.core.interfaces.extractor import Extractor
from vindex.core.interfaces.runtimes import SceneUnderstandingRuntime
from vindex.core.schemas.observations import (
    CaptionObservation,
    FrameObservation,
    ShotObservation,
)


class VLMCaptioner(Extractor):
    """Vision-Language Model (VLM) captioning extractor."""

    def __init__(self, runtime: Optional[SceneUnderstandingRuntime] = None) -> None:
        self.runtime = runtime

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[CaptionObservation]:
        """Generate captions for each shot using keyframe(s) and a vision-language model runtime."""
        if self.runtime is None:
            raise ValueError("VLMCaptioner requires a SceneUnderstandingRuntime injected during initialization.")

        shots = config.get("shots")
        frames = config.get("frames")


        if not shots or not frames:
            raise ValueError(
                "VLMCaptioner requires both 'shots' and 'frames' in the configuration dict."
            )

        # Parse and sort shots
        shot_list: list[ShotObservation] = []
        for s in shots:
            if isinstance(s, dict):
                shot_list.append(ShotObservation.model_validate(s))
            elif isinstance(s, ShotObservation):
                shot_list.append(s)
            else:
                raise TypeError(f"Invalid shot type in config: {type(s)}")

        # Parse frames
        frame_list: list[FrameObservation] = []
        for f in frames:
            if isinstance(f, dict):
                frame_list.append(FrameObservation.model_validate(f))
            elif isinstance(f, FrameObservation):
                frame_list.append(f)
            else:
                raise TypeError(f"Invalid frame type in config: {type(f)}")

        # Default prompt
        default_prompt = "Describe the scene in detail with complete sentences."
        prompt = config.get("prompt", default_prompt)

        ignore_text_regions = config.get("scene_understanding.ignore_text_regions", False)
        ocr_obs_list = config.get("ocr_obs", [])

        if ignore_text_regions:
            # Overwrite prompt to a clean positive instruction to avoid VLM negative constraint bias
            prompt = "Describe the scene in detail with complete sentences."




        # For each shot, find all frames belonging to it
        for shot in shot_list:
            shot_id = shot.shot_id
            
            # Find and potentially mask frames
            shot_frames: list[Path] = []
            temp_masked_paths: list[Path] = []
            
            for f in frame_list:
                if f.shot_id == shot_id:
                    frame_path = Path(f.frame_path)
                    
                    if ignore_text_regions and ocr_obs_list:
                        bboxes = []
                        for o in ocr_obs_list:
                            o_ref = o.get("frame_ref") if isinstance(o, dict) else getattr(o, "frame_ref", None)
                            o_bbox = o.get("bbox") if isinstance(o, dict) else getattr(o, "bbox", None)
                            if o_ref and Path(o_ref).resolve() == frame_path.resolve():
                                if o_bbox:
                                    bboxes.append(o_bbox)
                                    
                        if bboxes:
                            try:
                                import tempfile

                                from PIL import Image, ImageDraw
                                
                                with Image.open(frame_path) as img:
                                    img_rgb = img.convert("RGB") if img.mode != "RGB" else img
                                    
                                    draw = ImageDraw.Draw(img_rgb)
                                    width, height = img_rgb.size

                                    
                                    for bbox in bboxes:
                                        x, y, w, h = bbox
                                        if max(x, y, w, h) <= 1.0:
                                            x1 = x * width
                                            y1 = y * height
                                            x2 = (x + w) * width
                                            y2 = (y + h) * height
                                        else:
                                            x1 = x
                                            y1 = y
                                            x2 = x + w
                                            y2 = y + h
                                        draw.rectangle([x1, y1, x2, y2], fill="black")
                                    
                                    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                                    temp_path = Path(temp_file.name)
                                    temp_file.close()
                                    img_rgb.save(temp_path)
                                    shot_frames.append(temp_path)
                                    temp_masked_paths.append(temp_path)
                                    continue
                            except Exception:
                                # Fallback to original frame if masking fails
                                pass
                                
                    shot_frames.append(frame_path)

            if not shot_frames:
                # If no frames sampled for this shot, we cannot caption it. Log/skip.
                continue

            try:
                # Run VLM runtime
                caption_text = self.runtime.describe_scene(shot_frames, prompt, config)

                # Deduce model info from runtime id or config
                model_id = config.get("model_id", "unknown")
                model_version = config.get("model_version", "1.0")

                yield CaptionObservation(
                    schema_version="1.0",
                    timestamp_ms=shot.start_ms,
                    source=self.extractor_id,
                    shot_id=shot_id,
                    caption_text=caption_text,
                    model_id=model_id,
                    model_version=model_version,
                )
            finally:
                # Clean up temporary masked frame files
                for tmp_p in temp_masked_paths:
                    if tmp_p.exists():
                        try:
                            tmp_p.unlink()
                        except Exception:
                            pass


    @property
    def extractor_id(self) -> str:
        if self.runtime is not None:
            return f"vlm_caption.runtime.{self.runtime.runtime_id}"
        return "vlm_caption.unknown.v1"
