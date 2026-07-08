from pathlib import Path

import pytest

from vindex.compiler.scene_grouper import SceneGrouper, cosine_similarity
from vindex.core.interfaces.runtimes import SemanticEmbeddingRuntime
from vindex.core.schemas.artifacts import Shot
from vindex.core.schemas.observations import CaptionObservation
from vindex.runtimes.embedding.minilm_runtime import MiniLMEmbeddingRuntime


class MockEmbeddingRuntime(SemanticEmbeddingRuntime):
    """Mock embedding runtime for CI test isolation."""

    def __init__(self) -> None:
        # Maps text to predefined vectors
        self.vectors = {
            "apple": [1.0, 0.0, 0.0],
            "banana": [0.9, 0.1, 0.0],  # Similar to apple (high cosine)
            "car": [0.0, 1.0, 0.0],     # Dissimilar to apple/banana (low cosine)
            "": [0.0, 0.0, 0.0],
        }

    def load(self, model_dir_or_path: Path) -> None:
        pass

    def unload(self) -> None:
        pass

    def embed_text(self, texts: list[str], config: dict) -> list[list[float]]:
        res = []
        for t in texts:
            found = False
            for k, vec in self.vectors.items():
                if k and k in t:
                    res.append(vec)
                    found = True
                    break

            if not found:
                res.append([0.0, 0.0, 0.0])
        return res

    @property
    def runtime_id(self) -> str:
        return "mock_embed"


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)

    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v3) == pytest.approx(0.0)

    v4 = [0.707, 0.707, 0.0]
    assert cosine_similarity(v1, v4) == pytest.approx(0.707, abs=1e-3)


def test_scene_grouper_semantic_grouping():
    runtime = MockEmbeddingRuntime()
    grouper = SceneGrouper(runtime=runtime, similarity_threshold=0.65, max_gap_ms=2000)
    
    # We create 3 shots
    # Shot 1: "apple" at 0-1000
    # Shot 2: "banana" at 1000-2000 (similar to Shot 1, time gap 0 <= 2000) -> grouped
    # Shot 3: "car" at 2000-3000 (dissimilar, time gap 0) -> new scene
    c1 = CaptionObservation(schema_version="1.0", timestamp_ms=0, source="vlm", shot_id="sh1", caption_text="an apple", model_id="m1", model_version="v1")
    s1 = Shot(shot_id="sh1", start_ms=0, end_ms=1000, caption=c1)

    c2 = CaptionObservation(schema_version="1.0", timestamp_ms=1000, source="vlm", shot_id="sh2", caption_text="a banana", model_id="m1", model_version="v1")
    s2 = Shot(shot_id="sh2", start_ms=1000, end_ms=2000, caption=c2)

    c3 = CaptionObservation(schema_version="1.0", timestamp_ms=2000, source="vlm", shot_id="sh3", caption_text="a car", model_id="m1", model_version="v1")
    s3 = Shot(shot_id="sh3", start_ms=2000, end_ms=3000, caption=c3)

    scenes = grouper.group_scenes([s1, s2, s3], {})
    
    assert len(scenes) == 2
    
    # First scene: sh1 and sh2
    assert scenes[0].scene_id == "sc001"
    assert len(scenes[0].shots) == 2
    assert scenes[0].shots[0].shot_id == "sh1"
    assert scenes[0].shots[1].shot_id == "sh2"
    assert scenes[0].start_ms == 0
    assert scenes[0].end_ms == 2000
    assert scenes[0].dominant_caption == "an apple"
    
    # Second scene: sh3
    assert scenes[1].scene_id == "sc002"
    assert len(scenes[1].shots) == 1
    assert scenes[1].shots[0].shot_id == "sh3"
    assert scenes[1].start_ms == 2000
    assert scenes[1].end_ms == 3000
    assert scenes[1].dominant_caption == "a car"


def test_scene_grouper_time_gap_grouping():
    runtime = MockEmbeddingRuntime()
    # threshold 0.5, max_gap 1000ms
    grouper = SceneGrouper(runtime=runtime, similarity_threshold=0.5, max_gap_ms=1000)
    
    # Shot 1: "apple" at 0-1000
    # Shot 2: "banana" at 2500-3500 (similar, but time gap 1500 > 1000ms) -> should NOT group
    c1 = CaptionObservation(schema_version="1.0", timestamp_ms=0, source="vlm", shot_id="sh1", caption_text="apple", model_id="m1", model_version="v1")
    s1 = Shot(shot_id="sh1", start_ms=0, end_ms=1000, caption=c1)

    c2 = CaptionObservation(schema_version="1.0", timestamp_ms=2500, source="vlm", shot_id="sh2", caption_text="banana", model_id="m1", model_version="v1")
    s2 = Shot(shot_id="sh2", start_ms=2500, end_ms=3500, caption=c2)

    scenes = grouper.group_scenes([s1, s2], {})
    
    assert len(scenes) == 2


def test_minilm_runtime_no_model_dir_raises():
    runtime = MiniLMEmbeddingRuntime()
    with pytest.raises(ValueError, match="MiniLMEmbeddingRuntime requires 'model_dir'"):
        runtime.embed_text(["hello"], {})


def test_minilm_runtime_missing_model_dir_raises():
    runtime = MiniLMEmbeddingRuntime()
    with pytest.raises(FileNotFoundError, match="SentenceTransformer model weights not found"):
        runtime.embed_text(["hello"], {"model_dir": "/non_existent_path"})



def test_scene_grouper_speaker_continuity():
    # Setup:
    # Shot 1: caption "apple", ASR word "hello" at 100-500
    # Shot 2: caption "car" (dissimilar, similarity 0.0), ASR word "world" at 600-900 (silence gap 100ms <= 1500ms)
    # The normal similarity threshold is 0.65.
    # Due to speaker continuity, the threshold is lowered by 0.15 to 0.50.
    # Wait, the similarity between "apple" and "car" is 0.0, which is still below 0.50, so they shouldn't group.
    # But if Shot 2 has caption "banana" (similarity 0.9*1.0 + 0.1*0.0 = 0.9, which is high and groups anyway).
    # What if similarity is 0.55?
    # Let's verify: MockEmbeddingRuntime returns [1.0, 0.0, 0.0] for apple, [0.9, 0.1, 0.0] for banana. Cosine similarity is 0.9.
    # Let's mock a vector for "orange" [0.55, 0.835, 0.0]. Cosine similarity with apple [1, 0, 0] is 0.55.
    # Normal threshold is 0.65 -> does NOT group.
    # With speaker continuity, threshold is lowered to 0.50 -> Groups!
    
    runtime = MockEmbeddingRuntime()
    # Add orange mapping to mock runtime
    runtime.vectors["orange"] = [0.55, 0.835, 0.0]
    
    grouper = SceneGrouper(runtime=runtime, similarity_threshold=0.65, max_gap_ms=2000)
    
    from vindex.core.schemas.observations import ASRWordObservation
    w1 = ASRWordObservation(schema_version="1.0", timestamp_ms=100, source="asr", word="hello", start_ms=100, end_ms=500, confidence=1.0)
    w2 = ASRWordObservation(schema_version="1.0", timestamp_ms=600, source="asr", word="world", start_ms=600, end_ms=900, confidence=1.0)
    
    c1 = CaptionObservation(schema_version="1.0", timestamp_ms=0, source="vlm", shot_id="sh1", caption_text="an apple", model_id="m1", model_version="v1")
    s1 = Shot(shot_id="sh1", start_ms=0, end_ms=1000, caption=c1, asr_words=[w1])
    
    c2 = CaptionObservation(schema_version="1.0", timestamp_ms=1000, source="vlm", shot_id="sh2", caption_text="an orange", model_id="m1", model_version="v1")
    s2 = Shot(shot_id="sh2", start_ms=1000, end_ms=2000, caption=c2, asr_words=[w2])
    
    # 1. Without speaker continuity (silence gap is large)
    w2_far = ASRWordObservation(schema_version="1.0", timestamp_ms=3000, source="asr", word="world", start_ms=3000, end_ms=3500, confidence=1.0)
    s2_no_continuity = Shot(shot_id="sh2", start_ms=1000, end_ms=2000, caption=c2, asr_words=[w2_far])
    
    scenes_split = grouper.group_scenes([s1, s2_no_continuity], {})
    assert len(scenes_split) == 2  # Split because similarity 0.55 < 0.65
    
    # 2. With speaker continuity (silence gap is short 100ms <= 1500ms)
    scenes_grouped = grouper.group_scenes([s1, s2], {})
    assert len(scenes_grouped) == 1  # Grouped because threshold lowered to 0.50, and similarity 0.55 >= 0.50

