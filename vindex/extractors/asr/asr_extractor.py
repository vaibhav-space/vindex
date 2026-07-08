import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterator, Optional

from vindex.core.interfaces.extractor import Extractor
from vindex.core.interfaces.runtimes import ASRRuntime
from vindex.core.schemas.observations import ASRWordObservation


class ASRExtractor(Extractor):
    """Audio transcription extractor."""

    def __init__(self, runtime: Optional[ASRRuntime] = None) -> None:
        self.runtime = runtime

    def _extract(self, video_path: Path, config: dict[str, Any]) -> Iterator[ASRWordObservation]:
        """Transcribe the video's audio using passthrough or an ASR model runtime."""
        # Preferred mode: Passthrough transcript
        transcript_path_str = config.get("transcript_path")
        if transcript_path_str:
            transcript_path = Path(transcript_path_str)
            if not transcript_path.exists():
                raise FileNotFoundError(f"Transcript file not found: {transcript_path}")

            with open(transcript_path, "r") as f:
                data = json.load(f)

            words_list = data.get("words", [])
            for word_data in words_list:
                word = str(word_data["word"])
                # Start and end timestamps are in seconds in Whisper JSON, convert to ms
                start_ms = int(float(word_data["start"]) * 1000)
                end_ms = int(float(word_data["end"]) * 1000)
                confidence = float(word_data.get("confidence", 1.0))

                yield ASRWordObservation(
                    schema_version="1.0",
                    timestamp_ms=start_ms,
                    source=self.extractor_id,
                    word=word,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    confidence=confidence,
                )
            return

        # Fallback mode: Run ASR model runtime
        if self.runtime is None:
            raise ValueError(
                "ASRExtractor requires either a 'transcript_path' in the config "
                "or an ASRRuntime injected during initialization."
            )

        import av
        container = av.open(str(video_path))
        has_audio = len(container.streams.audio) > 0
        container.close()

        if not has_audio:
            # Video does not contain audio; skip ASR
            return

        # Extract audio using ffmpeg
        ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = Path(temp_wav.name)

        try:
            # ffmpeg command to extract mono 16kHz audio
            cmd = [
                ffmpeg_path,
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(temp_wav_path),
                "-y"
            ]
            
            # Hide output unless it fails
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"ffmpeg audio extraction failed: {res.stderr}")

            # Run ASR transcribe
            words = self.runtime.transcribe(temp_wav_path, config)
            
            for word_data in words:
                word = str(word_data["word"])
                # Timestamps from transcribe are also in seconds, convert to ms
                start_ms = int(float(word_data["start"]) * 1000)
                end_ms = int(float(word_data["end"]) * 1000)
                confidence = float(word_data.get("confidence", 1.0))

                yield ASRWordObservation(
                    schema_version="1.0",
                    timestamp_ms=start_ms,
                    source=self.extractor_id,
                    word=word,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    confidence=confidence,
                )

        finally:
            if temp_wav_path.exists():
                os.unlink(temp_wav_path)

    @property
    def extractor_id(self) -> str:
        if self.runtime is not None:
            return f"asr.runtime.{self.runtime.runtime_id}"
        return "asr.passthrough.v1"
