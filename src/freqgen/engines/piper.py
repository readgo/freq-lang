"""Piper TTS engine."""

import subprocess
import wave
from pathlib import Path

try:
    import pyogg
    PYOgg_AVAILABLE = True
except ImportError:
    PYOgg_AVAILABLE = False

from .base import GenerationResult, PauseRegion, SentenceResult, TTSEngine, WordTimestamp


def _discover_voices() -> list[str]:
    """Scan ~/.local/share/piper for all available voice names."""
    piper_dir = Path.home() / ".local/share/piper"
    if not piper_dir.exists():
        return []
    return sorted(p.stem for p in piper_dir.iterdir() if p.suffix == ".onnx")


class PiperEngine(TTSEngine):
    name = "piper"
    default_voice = None
    available_voices = []

    def __init__(self, model_path: str | Path | None = None, config_path: str | Path | None = None):
        self.available_voices = _discover_voices()
        if not self.available_voices:
            raise FileNotFoundError(
                "Piper voice not found. Download one like this:\n"
                "  python3 /home/jing/.local/lib/python3.12/site-packages/piper/download_voices.py en_US-lessac-medium --download-dir ~/.local/share/piper"
            )
        if model_path:
            self.model_path = Path(model_path)
        else:
            chosen = self.available_voices[0]
            self.model_path = Path.home() / ".local/share/piper" / f"{chosen}.onnx"
        self.default_voice = self.model_path.stem
        self.config_path = Path(config_path) if config_path else None

    def voices(self) -> list[str]:
        return self.available_voices

    def generate(self, text: str, voice: str, output_path: Path) -> GenerationResult:
        cmd = [
            "piper", "-m", str(self.model_path),
            "-f", str(output_path),
            "--cuda",
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
        result = self.generate(text, voice, output_path)
        words = self._estimate_word_timestamps(text, result.duration_s)
        pauses = self._find_pauses_wav(output_path)
        return SentenceResult(
            text=text,
            audio_path=output_path,
            duration_s=result.duration_s,
            sample_rate=result.sample_rate,
            words=words,
            pauses=pauses,
        )

    def _estimate_word_timestamps(self, text: str, duration: float) -> list[WordTimestamp]:
        words = text.replace(".", " . ").replace(",", " , ").replace("?", " ?").replace("!", " !").split()
        if not words:
            return []
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

    def _find_pauses_wav(self, wav_path: Path) -> list[PauseRegion]:
        """Detect silence regions >= 100ms in a wav file."""
        import numpy as np
        try:
            import soundfile as sf
            samples, sr = sf.read(str(wav_path))
        except Exception:
            return []
        return self._find_pauses(samples, sr)

    def _find_pauses(self, samples, sr: int) -> list[PauseRegion]:
        import numpy as np
        WINDOW = 0.020
        MIN_PAUSE = 0.100
        THRESHOLD_RATIO = 0.08

        window_len = int(WINDOW * sr)
        energy = []
        for i in range(0, len(samples), window_len):
            chunk = samples[i:i+window_len]
            if len(chunk) == 0:
                continue
            rms = np.sqrt(np.mean(chunk ** 2))
            energy.append(rms)

        if not energy:
            return []

        smoothed = []
        for j in range(len(energy)):
            window = energy[max(0, j - 2):j + 1]
            smoothed.append(np.mean(window))

        threshold = np.median(smoothed) * THRESHOLD_RATIO

        pauses = []
        in_pause = False
        pause_start = 0.0
        window_dur = window_len / sr

        for j, e in enumerate(smoothed):
            t = j * window_dur
            if e < threshold:
                if not in_pause:
                    pause_start = t
                    in_pause = True
            else:
                if in_pause:
                    dur = t - pause_start
                    if dur >= MIN_PAUSE:
                        pauses.append(PauseRegion(start_s=pause_start, end_s=t))
                    in_pause = False

        if in_pause:
            dur = (len(samples) / sr) - pause_start
            if dur >= MIN_PAUSE:
                pauses.append(PauseRegion(start_s=pause_start, end_s=len(samples) / sr))

        return pauses

    def _get_wav_duration(self, wav_path: Path) -> float:
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / rate
