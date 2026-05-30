"""Piper TTS engine."""

import subprocess
import wave
from pathlib import Path

try:
    import pyogg
    PYOgg_AVAILABLE = True
except ImportError:
    PYOgg_AVAILABLE = False

from .base import GenerationResult, SentenceResult, TTSEngine, WordTimestamp


class PiperEngine(TTSEngine):
    name = "piper"
    default_voice = "en_US-lessac-medium"
    available_voices = []  # dynamically loaded

    def __init__(self, model_path: str | Path, config_path: str | Path | None = None):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path) if config_path else None
        self._load_voices()

    def _load_voices(self):
        """Extract available voices from model name."""
        model_name = self.model_path.stem
        self.available_voices = [model_name]

    def generate(self, text: str, voice: str, output_path: Path) -> GenerationResult:
        cmd = [
            "piper", "-m", str(self.model_path),
            "-f", str(output_path),
            "--cuda",  # use GPU if available
        ]
        if self.config_path:
            cmd.extend(["-c", str(self.config_path)])
        proc = subprocess.run(
            cmd,
            input=text.encode(),
            capture_output=True, timeout=60
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Piper failed: {proc.stderr.decode()}")
        duration = self._get_wav_duration(output_path)
        return GenerationResult(audio_path=output_path, duration_s=duration, sample_rate=22050)

    def generate_with_timestamps(self, text: str, voice: str, output_path: Path) -> SentenceResult:
        # Piper doesn't natively support word timestamps
        # Fall back to espeak-ng based estimation
        result = self.generate(text, voice, output_path)
        words = self._estimate_word_timestamps(text, result.duration_s)
        return SentenceResult(
            text=text,
            audio_path=output_path,
            duration_s=result.duration_s,
            sample_rate=result.sample_rate,
            words=words,
        )

    def _estimate_word_timestamps(self, text: str, duration: float) -> list[WordTimestamp]:
        """Rough word timestamps using espeak-ng phoneme estimation."""
        words = text.replace(".", " . ").replace(",", " , ").replace("?", " ?").replace("!", " !").split()
        if not words:
            return []
        # Heuristic: divide duration equally among words
        # Punctuation gets minimal time
        punct_words = {".", ",", "?", "!"}
        word_count = sum(1 for w in words if w not in punct_words)
        if word_count == 0:
            return [WordTimestamp(word=text.strip(), start_s=0.0, end_s=duration)]
        
        avg_word_duration = duration / word_count
        timestamps = []
        current_time = 0.0
        for word in words:
            if word in punct_words:
                continue
            end_time = min(current_time + avg_word_duration, duration)
            timestamps.append(WordTimestamp(
                word=word,
                start_s=round(current_time, 3),
                end_s=round(end_time, 3),
            ))
            current_time = end_time
        if timestamps and current_time < duration:
            timestamps[-1] = WordTimestamp(
                word=timestamps[-1].word,
                start_s=timestamps[-1].start_s,
                end_s=duration,
            )
        return timestamps

    def _get_wav_duration(self, wav_path: Path) -> float:
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / rate
