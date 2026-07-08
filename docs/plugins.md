# Plugin System

vindex is built around a decoupled architecture where extractors and runtimes are separate. This makes it easy to replace underlying machine learning engines (e.g. swapping model providers, backends, or local vs cloud inference) without touching the extraction logic.

## Core Abstractions

There are two primary base classes to extend when adding new features:

1. **`Extractor` (`vindex/core/interfaces/extractor.py`)**
   - Coordinates the extraction stage for a specific modality.
   - Handles cache lookups automatically.
   - Defines a `_extract` method that returns an iterator of `BaseObservation`.

2. **`Runtime` (`vindex/core/interfaces/runtimes.py`)**
   - Implements the actual neural network inference or hardware acceleration.
   - Examples: `ASRRuntime`, `OCRRuntime`, `VisionRuntime`, `EmbeddingRuntime`, `LLMRuntime`.

---

## Writing a Custom Runtime Plugin

To write a custom ASR runtime, for instance, inherit from `ASRRuntime` and implement the abstract methods:

```python
from typing import Any, Iterator
from pathlib import Path
from vindex.core.interfaces.runtimes import ASRRuntime
from vindex.core.schemas.observations import ASRWordObservation

class MyASRRuntime(ASRRuntime):
    def transcribe(self, audio_path: Path, config: dict[str, Any]) -> Iterator[ASRWordObservation]:
        # Implement your transcription logic here
        pass

    @property
    def runtime_id(self) -> str:
        return "my_custom_asr_v1"
```

Then inject your custom runtime into the ASRExtractor:

```python
runtime = MyASRRuntime()
extractor = ASRExtractor(runtime=runtime)
```
