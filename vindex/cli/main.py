import json
from pathlib import Path
from typing import Optional

import typer

from vindex.compiler.pipeline import compile_video

app = typer.Typer(name="vindex", help="vindex — the open-source video knowledge compiler.")


@app.command()
def compile(
    video_path: Path = typer.Argument(..., help="Path to the video file to compile."),
    output_dir: Path = typer.Option(Path("./dist"), "--output-dir", "-o", help="Directory to save the compiled outputs."),
    transcript_path: Optional[Path] = typer.Option(None, "--transcript-path", "-t", help="Path to pre-existing Whisper transcript JSON."),
    use_cache: bool = typer.Option(True, help="Toggle local caching of extractor observations."),
    cache_dir: Optional[Path] = typer.Option(None, help="Custom local cache directory."),
    asr_model_dir: Optional[Path] = typer.Option(None, help="Local directory containing ASR model weights."),
    det_model_dir: Optional[Path] = typer.Option(None, help="Local directory containing OCR detection weights."),
    rec_model_dir: Optional[Path] = typer.Option(None, help="Local directory containing OCR recognition weights."),
    vlm_model_dir: Optional[Path] = typer.Option(None, help="Local directory containing VLM model weights."),
    embed_model_dir: Optional[Path] = typer.Option(None, help="Local directory containing text embedding weights."),
    similarity_threshold: float = typer.Option(0.65, help="Cosine similarity threshold for scene grouping."),
    max_gap_ms: int = typer.Option(5000, help="Maximum allowed silence/time gap within a scene in ms."),
    sampling_strategy: str = typer.Option("middle", help="Keyframe sampling strategy ('middle', 'first_last', 'uniform_n')."),
    uniform_n: int = typer.Option(3, help="Number of frames to sample if using 'uniform_n'."),
    stages: Optional[str] = typer.Option(None, "--stages", help="Comma-separated list of stages to run (e.g. scene,ocr,asr)."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to a TOML configuration file."),
) -> None:
    """Compile a video into a Visual Memory Index (JSON/Markdown)."""
    # Create configuration dict
    config_dict = {
        "use_cache": use_cache,
        "similarity_threshold": similarity_threshold,
        "max_gap_ms": max_gap_ms,
        "sampling_strategy": sampling_strategy,
        "uniform_n": uniform_n,
    }
    if transcript_path:
        config_dict["transcript_path"] = str(transcript_path)
    if cache_dir:
        config_dict["cache_dir"] = str(cache_dir)
    if asr_model_dir:
        config_dict["asr_model_dir"] = str(asr_model_dir)
    if det_model_dir:
        config_dict["det_model_dir"] = str(det_model_dir)
    if rec_model_dir:
        config_dict["rec_model_dir"] = str(rec_model_dir)
    if vlm_model_dir:
        config_dict["vlm_model_dir"] = str(vlm_model_dir)
    if embed_model_dir:
        config_dict["embed_model_dir"] = str(embed_model_dir)
    if stages:
        config_dict["stages"] = [s.strip() for s in stages.split(",") if s.strip()]

    if config:
        if not config.exists():
            typer.secho(f"Config file not found: {config}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        import tomllib
        with open(config, "rb") as f:
            toml_data = tomllib.load(f)
        for k, v in toml_data.items():
            config_dict[k] = v

    try:
        typer.echo(f"Compiling video: {video_path}...")
        visual_memory = compile_video(video_path, output_dir, config_dict)
        typer.echo(f"Compilation successful! Outputs saved to {output_dir}")
        typer.echo(f"Video Hash: {visual_memory.video_hash}")
        typer.echo(f"Scenes compiled: {len(visual_memory.timeline.scenes)}")
        typer.echo(f"Events derived: {len(visual_memory.timeline.events)}")
    except Exception as e:
        typer.secho(f"Error during compilation: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def eval(
    fixture_dir: Path = typer.Argument(..., help="Path to the golden fixture directory."),
    output_dir: Path = typer.Argument(..., help="Path to the compiled output directory to evaluate."),
) -> None:
    """Run the evaluation harness on a golden fixture compiled output."""
    from vindex.evaluation.evaluator import evaluate_fixture
    try:
        typer.echo(f"Evaluating output directory {output_dir} against fixture {fixture_dir}...")
        metrics = evaluate_fixture(fixture_dir, output_dir)

        typer.echo("-------------------------------------------------")
        typer.echo(f"Evaluation Results for: {fixture_dir.name}")
        typer.echo("-------------------------------------------------")
        typer.echo(f"ASR Accuracy (Jaccard): {metrics['asr_accuracy']:.2%}")
        typer.echo(f"OCR Accuracy (Jaccard): {metrics['ocr_accuracy']:.2%}")
        typer.echo(f"Scene Boundary Precision: {metrics['scene_precision']:.2%}")
        typer.echo(f"Scene Boundary Recall: {metrics['scene_recall']:.2%}")
        typer.echo(f"Scene Boundary F1: {metrics['scene_f1']:.2%}")
        typer.echo("-------------------------------------------------")

        overall = metrics["overall_score"]
        if metrics["pass"]:
            typer.secho(f"OVERALL SCORE: {overall:.2%} - PASS", fg=typer.colors.GREEN, bold=True)
        else:
            typer.secho(f"OVERALL SCORE: {overall:.2%} - FAIL (Requires >= 85.00%)", fg=typer.colors.RED, bold=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Error during evaluation: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def inspect(
    artifact_path: Path = typer.Argument(..., help="Path to a compiled JSON artifact to pretty-print.")
) -> None:
    """Pretty-print a compiled vindex artifact (JSON)."""
    if not artifact_path.exists():
        typer.secho(f"Artifact file not found: {artifact_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    try:
        with open(artifact_path, "r") as f:
            data = json.load(f)
        typer.echo(json.dumps(data, indent=2))
    except Exception as e:
        typer.secho(f"Error reading or parsing artifact: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def validate(
    artifact_path: Path = typer.Argument(..., help="Path to the JSON artifact file to validate."),
    schema_type: str = typer.Option("VisualMemory", "--type", "-t", help="Schema type to validate against (e.g. VisualMemory, Timeline, Scene, Shot).")
) -> None:
    """Validate a compiled JSON artifact against its Pydantic schema."""
    if not artifact_path.exists():
        typer.secho(f"Artifact file not found: {artifact_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        with open(artifact_path, "r") as f:
            data = json.load(f)

        # Select Pydantic model
        if schema_type == "VisualMemory":
            from vindex.core.schemas.artifacts import VisualMemory
            VisualMemory.model_validate(data)
        elif schema_type == "Timeline":
            from vindex.core.schemas.artifacts import Timeline
            Timeline.model_validate(data)
        elif schema_type == "Scene":
            from vindex.core.schemas.artifacts import Scene
            Scene.model_validate(data)
        elif schema_type == "Shot":
            from vindex.core.schemas.artifacts import Shot
            Shot.model_validate(data)
        else:
            typer.secho(f"Unsupported schema type: {schema_type}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        typer.secho("Validation successful! Artifact is clean and matches the schema.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Validation failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
