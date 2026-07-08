from pathlib import Path

from typer.testing import CliRunner

from vindex.cli.main import app
from vindex.evaluation.evaluator import calculate_jaccard, evaluate_fixture


def test_calculate_jaccard():
    assert calculate_jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert calculate_jaccard({"a"}, {"b"}) == 0.0
    assert calculate_jaccard(set(), set()) == 1.0


def test_evaluate_fixture_identical():
    fixture_dir = Path("eval/golden/fixture_001")
    # For identical comparison, we compare fixture_001 expected directory against itself
    output_dir = fixture_dir / "expected"
    
    metrics = evaluate_fixture(fixture_dir, output_dir)
    
    assert metrics["asr_accuracy"] == 1.0
    assert metrics["ocr_accuracy"] == 1.0
    assert metrics["scene_precision"] == 1.0
    assert metrics["scene_recall"] == 1.0
    assert metrics["scene_f1"] == 1.0
    assert metrics["overall_score"] == 1.0
    assert metrics["pass"] is True


def test_cli_eval_command():
    runner = CliRunner()
    fixture_dir = Path("eval/golden/fixture_001")
    output_dir = fixture_dir / "expected"
    
    result = runner.invoke(
        app,
        [
            "eval",
            str(fixture_dir),
            str(output_dir),
        ]
    )
    
    assert result.exit_code == 0
    assert "Evaluation Results for: fixture_001" in result.output
    assert "OVERALL SCORE: 100.00% - PASS" in result.output
