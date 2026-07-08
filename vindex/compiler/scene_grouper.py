import math
from typing import Any

from vindex.core.interfaces.runtimes import SemanticEmbeddingRuntime
from vindex.core.schemas.artifacts import Scene, Shot


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate the cosine similarity between two vector embeddings."""
    dot_product = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class SceneGrouper:
    """Groups consecutive Shots into semantically coherent Scenes using embeddings."""

    def __init__(
        self,
        runtime: SemanticEmbeddingRuntime,
        similarity_threshold: float = 0.65,
        max_gap_ms: int = 5000,
    ) -> None:
        self.runtime = runtime

        self.similarity_threshold = similarity_threshold
        self.max_gap_ms = max_gap_ms

    def group_scenes(self, shots: list[Shot], config: dict[str, Any]) -> list[Scene]:
        """Group chronological shots into scenes based on caption similarity and time proximity."""
        if not shots:
            return []

        # Ensure shots are sorted chronologically
        sorted_shots = sorted(shots, key=lambda x: x.start_ms)

        # Get captions for embedding
        captions = []
        for shot in sorted_shots:
            if shot.caption and shot.caption.caption_text:
                captions.append(shot.caption.caption_text)
            else:
                captions.append("")

        # Get embeddings from runtime using correct embed_model_dir
        embed_config = dict(config)
        if "embed_model_dir" in config:
            embed_config["model_dir"] = config["embed_model_dir"]
        embeddings = self.runtime.embed_text(captions, embed_config)


        threshold = config.get("similarity_threshold", self.similarity_threshold)
        max_gap = config.get("max_gap_ms", self.max_gap_ms)

        scenes: list[Scene] = []
        current_group = [sorted_shots[0]]

        for i in range(1, len(sorted_shots)):
            prev_shot = sorted_shots[i - 1]
            curr_shot = sorted_shots[i]
            time_gap = curr_shot.start_ms - prev_shot.end_ms
            similarity = cosine_similarity(embeddings[i - 1], embeddings[i])

            # Speaker continuity heuristic:
            # If the silence gap between last word of prev_shot and first word of curr_shot
            # is short, we assume continuous speech and lower the grouping threshold.
            speaker_continuous = True
            prev_words = sorted(prev_shot.asr_words, key=lambda w: w.end_ms)
            curr_words = sorted(curr_shot.asr_words, key=lambda w: w.start_ms)
            
            if prev_words and curr_words:
                last_word = prev_words[-1]
                first_word = curr_words[0]
                silence_gap = first_word.start_ms - last_word.end_ms
                if silence_gap > config.get("speaker_change_silence_ms", 1500):
                    speaker_continuous = False

            effective_threshold = threshold
            # Apply heuristic only if speech is active across shots
            if speaker_continuous and (prev_shot.asr_words or curr_shot.asr_words):
                effective_threshold = max(0.4, threshold - 0.15)

            if similarity >= effective_threshold and time_gap <= max_gap:
                current_group.append(curr_shot)
            else:
                scenes.append(self._create_scene(len(scenes) + 1, current_group))
                current_group = [curr_shot]

        # Finalize the last group
        if current_group:
            scenes.append(self._create_scene(len(scenes) + 1, current_group))

        return scenes

    def _create_scene(self, idx: int, group: list[Shot]) -> Scene:
        """Helper to construct a Scene model from a group of Shots."""
        scene_id = f"sc{idx:03d}"
        start_ms = group[0].start_ms
        end_ms = group[-1].end_ms

        # Find dominant caption (first non-empty shot caption)
        dominant_caption = None
        for shot in group:
            if shot.caption and shot.caption.caption_text:
                dominant_caption = shot.caption.caption_text
                break

        return Scene(
            scene_id=scene_id,
            shots=group,
            start_ms=start_ms,
            end_ms=end_ms,
            dominant_caption=dominant_caption,
        )
