import gc
from pathlib import Path
from typing import Any, Optional

from vindex.core.interfaces.runtimes import LLMRuntime, SceneUnderstandingRuntime


class MLXVLMRuntime(SceneUnderstandingRuntime, LLMRuntime):
    """VLM and LLM runtime using Qwen2.5-VL via mlx-vlm."""

    def __init__(self) -> None:
        self.model: Any = None
        self.processor: Any = None
        self.loaded_model_dir: Optional[Path] = None

    def load(self, model_dir_or_path: Path) -> None:
        """Load the model and processor locally into memory."""
        if self.model is not None and self.loaded_model_dir == model_dir_or_path:
            return  # Already loaded

        if not model_dir_or_path.is_dir() or not (model_dir_or_path / "config.json").exists():
            raise FileNotFoundError(
                f"MLX VLM model directory not found at: {model_dir_or_path}. "
                "Please download the weights and configure the local path. "
                "Auto-downloads are prohibited."
            )

        # Lazy import to avoid loading heavy MLX code at start
        from mlx_vlm import load
        
        # Load the model and processor
        self.model, self.processor = load(str(model_dir_or_path))
        self.loaded_model_dir = model_dir_or_path

    def unload(self) -> None:
        """Unload weights, trigger GC, and clear MLX Metal cache."""
        self.model = None
        self.processor = None
        self.loaded_model_dir = None
        gc.collect()
        try:
            import mlx.core as mx  # type: ignore[import-not-found]

            mx.metal.clear_cache()
            mx.clear_cache()
        except Exception:
            pass

    def describe_scene(self, frame_paths: list[Path], prompt: str, config: dict[str, Any]) -> str:
        """Generate a description of a shot given frames and a prompt."""
        model_dir_str = config.get("model_dir")
        if not model_dir_str:
            raise ValueError(
                "MLXVLMRuntime requires 'model_dir' to be configured."
            )

        model_path = Path(model_dir_str)
        self.load(model_path)

        if self.model is None or self.processor is None:
            raise RuntimeError("MLXVLM model was not loaded successfully.")

        from mlx_vlm import generate
        from mlx_vlm.utils import load_image

        # Load images from path strings
        images = [load_image(str(p)) for p in frame_paths]

        # Construct message format and apply chat template if processor supports it
        content = []
        for _ in range(len(images)):
            content.append({"type": "image"})
        content.append({"type": "text", "text": prompt})
        
        messages = [{"role": "user", "content": content}]
        formatted_prompt = prompt
        if self.processor is not None and hasattr(self.processor, "apply_chat_template"):
            try:
                formatted_prompt = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            except Exception:
                pass

        # Call generate. Standard MLX VLM generate handles list of images
        # We default to max_tokens=128 for captions
        max_tokens = config.get("max_tokens", 128)
        temp = config.get("temperature", 0.0)

        output = generate(
            self.model,
            self.processor,
            prompt=formatted_prompt,
            image=images,
            max_tokens=max_tokens,
            temperature=temp,
            repetition_penalty=1.2,
            repetition_context_size=64,
            verbose=False,
        )

        if hasattr(output, "text"):
            return str(output.text).strip()
        return str(output).strip()



    def generate(self, prompt: str, config: dict[str, Any]) -> str:
        """Generate text from a prompt (LLM mode, used by Narration)."""
        model_dir_str = config.get("model_dir")
        if not model_dir_str:
            raise ValueError(
                "MLXVLMRuntime requires 'model_dir' to be configured."
            )

        model_path = Path(model_dir_str)
        self.load(model_path)

        if self.model is None or self.processor is None:
            raise RuntimeError("MLXVLM model was not loaded successfully.")

        from mlx_vlm import generate

        # Construct message format and apply chat template if processor supports it
        max_tokens = config.get("max_tokens", 1024)
        temp = config.get("temperature", 0.0)
        messages = [{"role": "user", "content": prompt}]
        formatted_prompt = prompt
        if self.processor is not None and hasattr(self.processor, "apply_chat_template"):
            try:
                formatted_prompt = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            except Exception:
                pass


        output = generate(
            self.model,
            self.processor,
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            temperature=temp,
            repetition_penalty=1.2,
            repetition_context_size=64,
            verbose=False,
        )

        if hasattr(output, "text"):
            return str(output.text).strip()
        return str(output).strip()

    @property
    def runtime_id(self) -> str:
        return "mlx_vlm.v1"

