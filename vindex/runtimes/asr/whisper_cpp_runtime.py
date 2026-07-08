import json
import os
import subprocess
from pathlib import Path
from typing import Any

from vindex.core.interfaces.runtimes import ASRRuntime


class WhisperCppRuntime(ASRRuntime):
    """ASR runtime calling the whisper.cpp command line tool."""

    def load(self, model_dir_or_path: Path) -> None:
        """Validate paths if model weight is available."""
        if not model_dir_or_path.exists():
            raise FileNotFoundError(f"Model path not found: {model_dir_or_path}")

    def unload(self) -> None:
        """No-op for subprocess runtimes."""
        pass

    def transcribe(self, audio_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:

        """Transcribe audio using whisper.cpp binary via subprocess."""
        binary_path_str = config.get("binary_path")
        if not binary_path_str:
            raise ValueError(
                "WhisperCppRuntime requires 'binary_path' to be set in the config."
            )

        binary_path = Path(binary_path_str)
        if not binary_path.exists():
            raise FileNotFoundError(f"whisper.cpp binary not found at: {binary_path}")

        model_path_str = config.get("model_path") or config.get("model_dir")
        if not model_path_str:
            raise ValueError(
                "WhisperCppRuntime requires 'model_path' (or 'model_dir') in the config."
            )

        model_path = Path(model_path_str)
        if not model_path.exists():
            raise FileNotFoundError(f"Whisper model weights not found at: {model_path}")

        # JSON output will be saved at audio_path + '.json'
        # e.g. /tmp/temp.wav -> /tmp/temp.wav.json
        output_json_path = audio_path.with_name(f"{audio_path.name}.json")

        cmd = [
            str(binary_path),
            "-m", str(model_path),
            "-f", str(audio_path),
            "-oj",
            "-owts",
        ]

        # Add threads config if set
        threads = config.get("threads")
        if threads:
            cmd.extend(["-t", str(threads)])

        # Run whisper.cpp command
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"whisper.cpp execution failed: {res.stderr}")

        if not output_json_path.exists():
            raise FileNotFoundError(
                f"whisper.cpp output JSON file not generated: {output_json_path}"
            )

        try:
            with open(output_json_path, "r") as f:
                data = json.load(f)

            words_list = []
            transcription = data.get("transcription", [])
            for segment in transcription:
                tokens = segment.get("tokens", [])
                for token in tokens:
                    text = token.get("text", "").strip()
                    # Skip empty tokens or special tokens like [VC]
                    if not text or (text.startswith("[") and text.endswith("]")):
                        continue

                    offsets = token.get("offsets", {})
                    # offsets from and to are in milliseconds in whisper.cpp json, convert to seconds
                    start = float(offsets.get("from", 0)) / 1000.0
                    end = float(offsets.get("to", 0)) / 1000.0
                    
                    # p is token probability (0 to 100 or logprob depending on version)
                    # Convert to confidence between 0.0 and 1.0
                    p = float(token.get("p", 100))
                    confidence = p / 100.0 if p <= 100.0 else 1.0

                    words_list.append({
                        "word": text,
                        "start": start,
                        "end": end,
                        "confidence": confidence,
                    })

            return words_list

        finally:
            if output_json_path.exists():
                os.unlink(output_json_path)

    @property
    def runtime_id(self) -> str:
        return "whisper_cpp.v1"
