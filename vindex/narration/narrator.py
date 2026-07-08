from typing import Any

from vindex.core.interfaces.runtimes import LLMRuntime
from vindex.core.schemas.artifacts import VisualMemory


class Narrator:
    """Generates a Markdown narration of the compiled VisualMemory index using an LLM."""

    def __init__(self, runtime: LLMRuntime) -> None:
        self.runtime = runtime

    def narrate(self, visual_memory: VisualMemory, config: dict[str, Any]) -> str:
        """Narrate the compiled visual memory, strictly grounded in the JSON data."""
        model_id = config.get("model_id", "unknown")
        model_version = config.get("model_version", "1.0")

        # Build header
        markdown_parts = [
            "# Visual Memory Index\n",
            f"**Generated at:** {visual_memory.generated_at}",
            f"**Video Hash:** {visual_memory.video_hash}",
            f"**Narration Model:** {model_id} (version: {model_version})\n",
            "> [!NOTE]",
            "> The narration text below is non-deterministic LLM output strictly "
            "grounded in the compiled video index.\n",
            "---\n",
            "## Chronological Scenes\n"
        ]

        if not visual_memory.timeline.scenes:
            # Fallback for empty scenes list
            import json
            prompt = f"Describe the video. The video contains no scenes. Timeline: {json.dumps(visual_memory.timeline.model_dump())}"
            narration_text = self.runtime.generate(prompt, config)
            return "\n".join(markdown_parts) + "\n" + narration_text



        # Process each scene sequentially

        for scene in visual_memory.timeline.scenes:
            scene_id = scene.scene_id
            start_sec = scene.start_ms / 1000.0
            end_sec = scene.end_ms / 1000.0

            # Gather observations across shots
            caption_texts = []
            ocr_words = []
            asr_words = []

            for shot in scene.shots:
                if shot.caption and shot.caption.caption_text:
                    caption_texts.append(shot.caption.caption_text)
                if shot.ocr:
                    ocr_words.extend([o.text for o in shot.ocr if o.text])
                if shot.asr_words:
                    asr_words.extend([a.word.strip() for a in shot.asr_words if a.word])

            # Deduplicate and clean
            vlm_caption = " ".join(caption_texts) if caption_texts else "(None)"
            ocr_text = ", ".join(list(dict.fromkeys(ocr_words))[:10]) if ocr_words else "(None)"
            asr_sentence = " ".join(asr_words) if asr_words else "(None)"

            # Construct focused prompt for the scene narration
            prompt = (
                "You are a factual video narrator. Write a brief single-paragraph narration summary (1-3 sentences) "
                "for the video scene based ONLY on these compiled observations:\n"
                f"- Visual Caption: {vlm_caption}\n"
                f"- Screen Text (OCR): {ocr_text}\n"
                f"- Spoken Audio (ASR): {asr_sentence}\n\n"
                "Instructions:\n"
                "1. Synthesize the observations into a natural paragraph description.\n"
                "2. Be concise and factual. Do not make assumptions or invent details beyond the observations.\n"
                "3. If all observations are empty or (None), state that the scene contains no visual or audio events.\n"
                "4. Output only the narration paragraph text directly."
            )

            # Generate narration for this scene using the LLM runtime
            # Override max_tokens to keep the scene narration concise
            scene_config = dict(config)
            scene_config["max_tokens"] = 128
            narration_para = self.runtime.generate(prompt, scene_config).strip()

            # Append structured scene markdown
            markdown_parts.extend([
                f"### Scene {scene_id} [{start_sec:.2f}s - {end_sec:.2f}s]",
                f"- **VLM Caption:** {vlm_caption}",
                f"- **Screen Text (OCR):** {ocr_text}",
                f"- **Spoken Audio (ASR):** {asr_sentence}\n",
                "**Narration:**",
                f"{narration_para}\n",
                "---"
            ])

        return "\n".join(markdown_parts)

