# Narration Layer

The Narration layer provides a natural language Markdown description of the compiled video index. It utilizes an LLM runtime to translate structured JSON timelines and events into a readable narrative while enforcing strict factual grounding.

## Class Details

- **Implementation:** `Narrator`
- **Path:** `vindex/narration/narrator.py`

## Preamble Notice

Every generated `visual_memory.md` starts with a standard preamble block detailing the compilation context, model version, and a non-deterministic disclaimer:

```markdown
# Visual Memory Index

**Generated at:** 2026-07-08T00:00:00Z
**Video Hash:** hash_001
**Narration Model:** test-gpt-4 (version: v2)

> [!NOTE]
> The narration text below is non-deterministic LLM output strictly grounded in the compiled video index.
```

## Inputs and Configuration

The `narrate` method accepts:
1. `visual_memory: VisualMemory` — The top-level compiled output artifact.
2. `config: dict[str, Any]` — Configuration dictionary containing:
   - `model_id: str` — Name/ID of the LLM model used.
   - `model_version: str` — Version of the LLM model used.
   - `max_tokens: int` (default `1024`) — Maximum generation limit.
   - `temperature: float` (default `0.0`) — LLM temperature (must be low for grounding).

## Prompt Design and Grounding

The prompt explicitly tells the LLM to write a chronological description based *only* on the provided JSON index, reference scenes by ID and time range, and omit hypothetical or speculative assertions. It enforces that no outside facts or hallucinations are included.
