"""TTS factory — switch providers via TTS_PROVIDER env or constructor arg"""
from __future__ import annotations

import os
from .base import BaseTTS, TTSProviderError
from .kokoro import KokoroTTS, KOKORO_AVAILABLE, VOICES as KOKORO_VOICES
from .piper import PiperTTS, PIPER_AVAILABLE


def get_tts(provider: str | None = None, **kwargs) -> BaseTTS:
    """
    Return a TTS instance.

    Provider is resolved in this order:
    1. Explicit ``provider`` argument
    2. TTS_PROVIDER env variable
    3. Default: kokoro (if available), else piper

    Raises TTSProviderError if the provider is unknown or unavailable.
    """
    if provider is None:
        provider = os.getenv("TTS_PROVIDER", "").lower()

    if not provider:
        # Auto-select: Kokoro if installed, else Piper
        if KOKORO_AVAILABLE:
            provider = "kokoro"
        elif PIPER_AVAILABLE:
            provider = "piper"
        else:
            raise TTSProviderError(
                "No TTS provider available. Install kokoro-onnx (pip install kokoro-onnx soundfile) "
                "or piper-tts (pip install piper-tts)"
            )

    if provider == "kokoro":
        if not KOKORO_AVAILABLE:
            raise TTSProviderError("Kokoro-ONNX not installed. Run: pip install kokoro-onnx soundfile")
        return KokoroTTS(**kwargs)

    if provider == "piper":
        if not PIPER_AVAILABLE:
            raise TTSProviderError("piper-tts not installed. Run: pip install piper-tts")
        return PiperTTS(**kwargs)

    raise TTSProviderError(
        f"Unknown TTS provider: {provider!r}. Valid: kokoro, piper"
    )


def list_tts_providers() -> list[dict]:
    """Return info about all available providers"""
    providers = []
    if KOKORO_AVAILABLE:
        providers.append({
            "name": "kokoro",
            "display": "Kokoro-ONNX",
            "tag": "Highest quality English, MIT, ~300MB",
            "voices": [v for v in KokoroTTS.list_voices()],
        })
    if PIPER_AVAILABLE:
        providers.append({
            "name": "piper",
            "display": "Piper",
            "tag": "100+ voices, GPL, CPU-friendly",
            "models": PiperTTS.available_models(),
        })
    return providers
