import json
from pathlib import Path
from typing import Any


def calculate_jaccard(set1: set[str], set2: set[str]) -> float:
    if not set1 and not set2:
        return 1.0
    union = set1.union(set2)
    intersection = set1.intersection(set2)
    return len(intersection) / len(union)


def evaluate_fixture(fixture_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Compare compiled outputs in output_dir against the expected stubs in fixture_dir."""
    expected_dir = fixture_dir / "expected"

    # 1. Evaluate ASR
    with open(expected_dir / "asr.json", "r") as f:
        expected_asr = json.load(f)
    with open(output_dir / "asr.json", "r") as f:
        output_asr = json.load(f)

    exp_asr_words = set(w["word"].lower() for w in expected_asr)
    out_asr_words = set(w["word"].lower() for w in output_asr)
    asr_score = calculate_jaccard(exp_asr_words, out_asr_words)

    # 2. Evaluate OCR
    with open(expected_dir / "ocr.json", "r") as f:
        expected_ocr = json.load(f)
    with open(output_dir / "ocr.json", "r") as f:
        output_ocr = json.load(f)

    exp_ocr_text = set(" ".join(o["text"].lower().split()) for o in expected_ocr)
    out_ocr_text = set(" ".join(o["text"].lower().split()) for o in output_ocr)
    ocr_score = calculate_jaccard(exp_ocr_text, out_ocr_text)

    # 3. Evaluate Scene boundaries
    with open(expected_dir / "timeline.json", "r") as f:
        expected_timeline = json.load(f)
    with open(output_dir / "timeline.json", "r") as f:
        output_timeline = json.load(f)

    # Get boundary end times for all scenes (except the last one)
    exp_boundaries = set(s["end_ms"] for s in expected_timeline.get("scenes", [])[:-1])
    out_boundaries = set(s["end_ms"] for s in output_timeline.get("scenes", [])[:-1])

    # Calculate match with 500ms tolerance
    matched = 0
    tolerance = 500
    for ob in out_boundaries:
        for eb in exp_boundaries:
            if abs(ob - eb) <= tolerance:
                matched += 1
                break

    scene_precision = matched / len(out_boundaries) if out_boundaries else 1.0
    scene_recall = matched / len(exp_boundaries) if exp_boundaries else 1.0
    scene_f1 = (
        2 * (scene_precision * scene_recall) / (scene_precision + scene_recall)
        if (scene_precision + scene_recall) > 0
        else 1.0
    )

    # Overall Score is average of metrics
    overall = (asr_score + ocr_score + scene_f1) / 3.0

    return {
        "asr_accuracy": asr_score,
        "ocr_accuracy": ocr_score,
        "scene_precision": scene_precision,
        "scene_recall": scene_recall,
        "scene_f1": scene_f1,
        "overall_score": overall,
        "pass": overall >= 0.85,
    }
