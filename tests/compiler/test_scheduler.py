from unittest.mock import MagicMock, patch

from vindex.compiler.scheduler import RUNTIME_REGISTRY, ExecutionScheduler
from vindex.runtimes.asr.faster_whisper_runtime import FasterWhisperRuntime
from vindex.runtimes.vision.mlx_vlm_runtime import MLXVLMRuntime


def test_scheduler_registry_lookup():
    ExecutionScheduler()
    
    # Assert expected runtime mappings are present
    assert "asr.faster_whisper" in RUNTIME_REGISTRY
    assert "scene.mlx_vlm" in RUNTIME_REGISTRY
    assert "ocr.paddleocr" in RUNTIME_REGISTRY



@patch("vindex.runtimes.asr.faster_whisper_runtime.WhisperModel")
@patch("mlx_vlm.load")
def test_scheduler_sequential_gate(mock_vlm_load, mock_whisper, tmp_path):

    mock_whisper.return_value = MagicMock()
    mock_vlm_load.return_value = (MagicMock(), MagicMock())

    scheduler = ExecutionScheduler()
    
    # Create empty dummy directories to satisfy checks
    fw_dir = tmp_path / "fw_model"
    fw_dir.mkdir()
    (fw_dir / "model.bin").touch()
    
    vlm_dir = tmp_path / "vlm_model"
    vlm_dir.mkdir()
    (vlm_dir / "config.json").touch()

    # Load first model (FasterWhisper)
    runtime1 = scheduler.acquire_runtime("asr.faster_whisper", fw_dir)
    assert isinstance(runtime1, FasterWhisperRuntime)
    assert scheduler.active_runtime_key == "asr.faster_whisper"
    assert scheduler.active_runtime is runtime1
    
    # Load second model (MLXVLM) - should trigger release and unload on runtime1
    runtime2 = scheduler.acquire_runtime("scene.mlx_vlm", vlm_dir)
    assert isinstance(runtime2, MLXVLMRuntime)
    assert scheduler.active_runtime_key == "scene.mlx_vlm"
    assert scheduler.active_runtime is runtime2
    
    # Assert first runtime model reference is cleared
    assert runtime1.model is None
    
    # Release active
    scheduler.release_active()
    assert scheduler.active_runtime is None
    assert scheduler.active_runtime_key is None
    assert runtime2.model is None

