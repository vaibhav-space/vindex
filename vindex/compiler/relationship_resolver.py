from typing import Any

from vindex.core.schemas.artifacts import Relationship, Shot


class RelationshipResolver:
    """Resolves spatial/temporal relationships between different observations."""

    def resolve_relationships(self, shots: list[Shot], config: dict[str, Any]) -> list[Relationship]:
        """Identify relationships between OCR text, captions, and other shot elements."""
        relationships: list[Relationship] = []
        rel_counter = 1

        for shot in shots:
            if not shot.caption or not shot.ocr:
                continue

            caption_text = shot.caption.caption_text.lower()
            caption_words = set(caption_text.split())

            for ocr_obs in shot.ocr:
                # 1. Temporal overlap: since they belong to the same shot, they overlap temporally.
                rel_id = f"rel{rel_counter:03d}"
                relationships.append(
                    Relationship(
                        relationship_id=rel_id,
                        source_id=ocr_obs.source,  # source identifier
                        target_id=shot.caption.source,
                        relationship_type="temporal_overlap",
                        metadata={
                            "shot_id": shot.shot_id,
                            "timestamp_ms": ocr_obs.timestamp_ms,
                        },
                    )
                )
                rel_counter += 1

                # 2. Semantic matching: check if caption mentions words detected via OCR
                ocr_words = set(ocr_obs.text.lower().split())
                overlap = caption_words.intersection(ocr_words)

                # Skip small stop words like 'a', 'the', 'is', 'on', 'of', etc.
                stop_words = {"a", "an", "the", "is", "are", "on", "in", "of", "and", "or", "to", "at", "for", "with"}
                meaningful_overlap = overlap - stop_words

                if meaningful_overlap:
                    rel_id = f"rel{rel_counter:03d}"
                    relationships.append(
                        Relationship(
                            relationship_id=rel_id,
                            source_id=ocr_obs.source,
                            target_id=shot.caption.source,
                            relationship_type="ocr_caption_match",
                            metadata={
                                "shot_id": shot.shot_id,
                                "matched_words": list(meaningful_overlap),
                            },
                        )
                    )
                    rel_counter += 1

        return relationships
