from vindex.compiler.relationship_resolver import RelationshipResolver
from vindex.core.schemas.artifacts import Shot
from vindex.core.schemas.observations import CaptionObservation, OCRObservation


def test_resolve_relationships_happy_path():
    # Setup shot with caption and OCR
    caption = CaptionObservation(
        schema_version="1.0",
        timestamp_ms=0,
        source="vlm",
        shot_id="sh001",
        caption_text="A standard SMPTE color bar display with a solid test pattern.",
        model_id="qwen",
        model_version="1.0"
    )
    ocr = [
        OCRObservation(
            schema_version="1.0",
            timestamp_ms=1000,
            source="ocr",
            text="SMPTE",
            bbox=[0, 0, 10, 10],
            frame_ref="f1.png",
            confidence=0.95
        ),
        OCRObservation(
            schema_version="1.0",
            timestamp_ms=2000,
            source="ocr",
            text="UnknownText",
            bbox=[0, 0, 10, 10],
            frame_ref="f2.png",
            confidence=0.99
        )
    ]
    shot = Shot(
        shot_id="sh001",
        start_ms=0,
        end_ms=5000,
        frames=[],
        asr_words=[],
        ocr=ocr,
        caption=caption
    )

    resolver = RelationshipResolver()
    rels = resolver.resolve_relationships([shot], {})

    # Expected:
    # 2 temporal overlap relationships
    # 1 semantic match (since SMPTE overlaps caption text)
    assert len(rels) == 3

    temporal_rels = [r for r in rels if r.relationship_type == "temporal_overlap"]
    match_rels = [r for r in rels if r.relationship_type == "ocr_caption_match"]

    assert len(temporal_rels) == 2
    assert len(match_rels) == 1

    assert match_rels[0].metadata["matched_words"] == ["smpte"]
