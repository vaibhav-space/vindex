import gc
import logging
from pathlib import Path
from typing import Any, Optional, cast

from vindex.core.interfaces.runtimes import RuntimePlugin
from vindex.runtimes.asr.faster_whisper_runtime import FasterWhisperRuntime
from vindex.runtimes.asr.whisper_cpp_runtime import WhisperCppRuntime
from vindex.runtimes.embedding.minilm_runtime import MiniLMEmbeddingRuntime
from vindex.runtimes.motion.opencv_runtime import OpenCVFlowRuntime
from vindex.runtimes.objects.yolov8_runtime import YOLOv8ObjectDetectionRuntime
from vindex.runtimes.ocr.paddleocr_runtime import PaddleOCRRuntime
from vindex.runtimes.vision.mlx_vlm_runtime import MLXVLMRuntime

logger = logging.getLogger("vindex.scheduler")

# Runtime Registry Map (v2.0 decoupling core from model names)
RUNTIME_REGISTRY = {
    "asr.faster_whisper": FasterWhisperRuntime,
    "asr.whisper_cpp": WhisperCppRuntime,
    "ocr.paddleocr": PaddleOCRRuntime,
    "scene.mlx_vlm": MLXVLMRuntime,
    "llm.mlx_vlm": MLXVLMRuntime,
    "embed.minilm": MiniLMEmbeddingRuntime,
    "object.yolov8": YOLOv8ObjectDetectionRuntime,
    "motion.opencv": OpenCVFlowRuntime,
}



class ExecutionScheduler:
    """Manages sequential model lifecycle execution (load, unload, run, gc) under strict memory bounds."""

    def __init__(self) -> None:
        self.active_runtime: Optional[RuntimePlugin] = None
        self.active_runtime_key: Optional[str] = None

    def acquire_runtime(self, registry_key: str, model_dir_or_path: Path) -> RuntimePlugin:
        """Sequential acquisition gate: unloads any active runtime before loading the new one."""
        if self.active_runtime_key == registry_key and self.active_runtime is not None:
            return self.active_runtime

        self.release_active()

        if registry_key not in RUNTIME_REGISTRY:
            raise KeyError(f"Runtime '{registry_key}' not found in runtime registry.")

        runtime_cls = RUNTIME_REGISTRY[registry_key]
        runtime = cast(RuntimePlugin, cast(Any, runtime_cls)())


        logger.info(f"Loading runtime: {registry_key} from {model_dir_or_path}")
        runtime.load(model_dir_or_path)

        self.active_runtime = runtime
        self.active_runtime_key = registry_key
        return runtime

    def release_active(self) -> None:
        """Unload active runtime and trigger eager garbage collection."""
        if self.active_runtime is not None:
            logger.info(f"Unloading runtime: {self.active_runtime_key}")
            try:
                self.active_runtime.unload()
            except Exception as e:
                logger.warning(f"Error unloading runtime {self.active_runtime_key}: {e}")
            self.active_runtime = None
            self.active_runtime_key = None
            
            # Eager memory purge
            gc.collect()
            try:
                import mlx.core as mx  # type: ignore[import-not-found]

                mx.metal.clear_cache()
                mx.clear_cache()
            except ImportError:
                pass
            except Exception:
                pass
