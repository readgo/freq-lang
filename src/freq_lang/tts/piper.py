"""Piper local TTS — mature, 100+ voices, GPL licensed"""
from __future__ import annotations

import json
import os
import subprocess
import wave
from pathlib import Path

from .base import BaseTTS, TTSProviderError

try:
    import piper.voice as pv
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False


# Model configs for common English voices
MODEL_CONFIGS = {
    "en_US-lessac-medium": {
        "path": "en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "json": "en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    },
    "en_US-lessac-low": {
        "path": "en/en_US/lessac/low/en_US-lessac-low.onnx",
        "json": "en/en_US/lessac/low/en_US-lessac-low.onnx.json",
    },
    "en_GB-cori-medium": {
        "path": "en/en_GB/cori/medium/en_GB-cori-medium.onnx",
        "json": "en/en_GB/cori/medium/en_GB-cori-medium.onnx.json",
    },
    "en_GB-alan-medium": {
        "path": "en/en_GB/alan/medium/en_GB-alan-medium.onnx",
        "json": "en/en_GB/alan/medium/en_GB-alan-medium.onnx.json",
    },
}

HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
DEFAULT_MODEL = "en_US-lessac-medium"


class PiperTTS(BaseTTS):
    """Piper local neural TTS"""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        data_dir: Path | str | None = None,
    ):
        if not PIPER_AVAILABLE:
            raise TTSProviderError("piper-tts not installed. Run: pip install piper-tts")

        self.model_name = model
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            env_dir = os.getenv("PIPER_DATA_DIR")
            self.data_dir = Path(env_dir) if env_dir else Path(__file__).parent.parent.parent.parent / "models" / "piper"
        self._voice: pv.PiperVoice | None = None

    def _ensure_voice(self) -> pv.PiperVoice:
        if self._voice is not None:
            return self._voice

        model_info = MODEL_CONFIGS.get(self.model_name)
        if not model_info:
            raise TTSProviderError(f"Unknown Piper model: {self.model_name}. Available: {list(MODEL_CONFIGS.keys())}")

        onnx_path = self.data_dir / f"{self.model_name}.onnx"
        json_path = self.data_dir / f"{self.model_name}.onnx.json"

        if not onnx_path.exists() or not json_path.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Downloading Piper model: {self.model_name}")
            import urllib.request
            for rel in [model_info["path"], model_info["json"]]:
                dest_name = rel.rsplit("/", 1)[-1]
                dest = self.data_dir / dest_name
                if dest.exists():
                    continue
                url = f"{HF_BASE}/{rel}?download=true"
                print(f"    {dest_name}")
                urllib.request.urlretrieve(url, dest)

        self._voice = pv.PiperVoice.load(
            str(onnx_path),
            config_path=str(json_path),
            download_dir=str(self.data_dir),
        )
        return self._voice

    def synthesize(self, text: str, output: Path) -> None:
        voice = self._ensure_voice()
        tmp_wav = Path(f"/tmp/piper_{hash(text)}.wav")
        try:
            with wave.open(str(tmp_wav), "wb") as wav_f:
                wav_f.setnchannels(1)
                wav_f.setsampwidth(2)
                wav_f.setframerate(22050)
                for chunk in voice.synthesize(text):
                    wav_f.writeframes(chunk.audio_int16_array.tobytes())
            self._wav_to_mp3(tmp_wav, output)
        finally:
            tmp_wav.unlink(missing_ok=True)

    def _wav_to_mp3(self, wav_path: Path, mp3_path: Path) -> None:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav_path),
             "-codec:a", "libmp3lame", "-b:a", "128k", str(mp3_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise TTSProviderError(f"ffmpeg failed: {result.stderr.strip()}")

    @staticmethod
    def available_models() -> list[str]:
        return list(MODEL_CONFIGS.keys())

    @staticmethod
    def is_available() -> bool:
        return PIPER_AVAILABLE
