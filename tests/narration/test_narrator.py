from pathlib import Path

from vindex.core.interfaces.runtimes import LLMRuntime
from vindex.core.schemas.artifacts import Timeline, VisualMemory
from vindex.narration.narrator import Narrator


class MockLLMRuntime(LLMRuntime):
    """Mock LLM runtime for narration tests."""

    def __init__(self) -> None:
        self.last_prompt = ""

    def load(self, model_dir_or_path: Path) -> None:
        pass

    def unload(self) -> None:
        pass

    def generate(self, prompt: str, config: dict) -> str:
        self.last_prompt = prompt
        return "## Scene 1\nThis is a narrative description of the color bars."

    @property
    def runtime_id(self) -> str:
        return "mock_llm"



def test_narrator_happy_path():
    runtime = MockLLMRuntime()
    narrator = Narrator(runtime=runtime)
    
    timeline = Timeline(
        schema_version="1.0",
        video_hash="hash_001",
        scenes=[],
        events=[],
        total_duration_ms=5000,
    )
    visual_memory = VisualMemory(
        schema_version="1.0",
        video_hash="hash_001",
        generated_at="2026-07-08T00:00:00Z",
        timeline=timeline,
        metadata={},
    )
    
    config = {
        "model_id": "test-gpt-4",
        "model_version": "v2",
    }
    
    markdown = narrator.narrate(visual_memory, config)
    
    # Verify preamble structure
    assert "# Visual Memory Index" in markdown
    assert "**Generated at:** 2026-07-08T00:00:00Z" in markdown
    assert "**Video Hash:** hash_001" in markdown
    assert "**Narration Model:** test-gpt-4 (version: v2)" in markdown
    assert "> The narration text below is non-deterministic LLM output" in markdown
    
    # Verify LLM output is appended
    assert "This is a narrative description of the color bars." in markdown
    
    # Verify prompt contains compiled json
    assert "hash_001" in runtime.last_prompt
    assert "total_duration_ms" in runtime.last_prompt
