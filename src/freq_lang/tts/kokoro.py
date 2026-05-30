"""Kokoro-ONNX TTS — highest quality English TTS, MIT license, ~300MB"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .base import BaseTTS, TTSProviderError

try:
    from kokoro_onnx import Kokoro
    import soundfile as sf
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False


# Voice catalog — (id, display_name, lang)
# Full list: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
VOICES = {
    "af_sarah":   ("af_sarah",   "Sarah (American female)",   "en-us"),
    "af_brief":   ("af_brief",   "Brief (American female)",   "en-us"),
    "af_nicole":  ("af_nicole",  "Nicole (American female)",   "en-us"),
    "af_sky":     ("af_sky",     "Sky (American female)",      "en-us"),
    "bf_emma":    ("bf_emma",    "Emma (British female)",      "en-gb"),
    "bf_isabella":("bf_isabella","Isabella (British female)",  "en-gb"),
    "bm_george":  ("bm_george",  "George (British male)",      "en-gb"),
    "bm_lewis":   ("bm_lewis",   "Lewis (British male)",       "en-gb"),
}

DEFAULT_VOICE = "af_sarah"

# Model download URLs (GitHub releases)
MODEL_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"


class KokoroTTS(BaseTTS):
    """Kokoro-ONNX TTS provider"""

    def __init__(
        self,
        model_path: Path | str | None = None,
        voices_path: Path | str | None = None,
        voice: str = DEFAULT_VOICE,
    ):
        if not KOKORO_AVAILABLE:
            raise TTSProviderError(
                "kokoro-onnx not installed. Run: pip install kokoro-onnx soundfile"
            )

        self.model_path = self._resolve_path(
            model_path, os.getenv("KOKORO_MODEL_PATH"), "kokoro-v1.0.onnx"
        )
        self.voices_path = self._resolve_path(
            voices_path, os.getenv("KOKORO_VOICES_PATH"), "voices-v1.0.bin"
        )
        self.voice = voice
        self._kokoro: Kokoro | None = None

    def _resolve_path(self, explicit: Path | str | None, env: str | None, default: str) -> Path:
        if explicit:
            return Path(explicit)
        if env:
            return Path(env)
        # Default to models/kokoro/ in the project directory
        default_dir = Path(__file__).parent.parent.parent.parent / "models" / "kokoro"
        return default_dir / default

    def _ensure_model(self) -> Kokoro:
        if self._kokoro is not None:
            return self._kokoro

        if not self.model_path.exists():
            self._download_model(self.model_path, "kokoro-v1.0.onnx")
        if not self.voices_path.exists():
            self._download_model(self.voices_path, "voices-v1.0.bin")

        self._kokoro = Kokoro(str(self.model_path), str(self.voices_path))
        return self._kokoro

    def _download_model(self, dest: Path, filename: str) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"{MODEL_BASE}/{filename}?download=true"
        print(f"  Downloading {filename}...")
        subprocess.run(
            ["curl", "-L", "-o", str(dest), url],
            check=True,
            capture_output=True,
        )

    def synthesize(self, text: str, output: Path) -> None:
        kokoro = self._ensure_model()

        lang = "en-us"
        if self.voice.startswith("bf_") or self.voice.startswith("bm_"):
            lang = "en-gb"

        samples, sample_rate = kokoro.create(text, voice=self.voice, speed=1.0, lang=lang)

        # Kokoro returns float32 samples — write WAV directly then convert to MP3
        import wave
        tmp_wav = Path(f"/tmp/kokoro_{hash(text)}.wav")
        try:
            with wave.open(str(tmp_wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                # float32 -> int16
                import numpy as np
                int16 = (np.array(samples, dtype=np.float32) * 32767).astype(np.int16)
                wf.writeframes(int16.tobytes())

            self._wav_to_mp3(tmp_wav, output)
        finally:
            tmp_wav.unlink(missing_ok=True)

    def _wav_to_mp3(self, wav_path: Path, mp3_path: Path) -> None:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav_path),
             "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise TTSProviderError(f"ffmpeg failed: {result.stderr.strip()}")

    @staticmethod
    def list_voices() -> list[dict]:
        return [
            {"id": vid, "display": disp, "lang": lang}
            for vid, (_, disp, lang) in VOICES.items()
        ]

    @staticmethod
    def is_available() -> bool:
        return KOKORO_AVAILABLE
