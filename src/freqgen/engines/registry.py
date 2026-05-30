"""TTS engine registry."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from .base import TTSEngine
from .kokoro import KokoroEngine
from .piper import PiperEngine

_ENGINE_REGISTRY: dict[str, type[TTSEngine]] = {}


def register_engine(name: str):
    """Decorator to register a TTS engine."""
    def deco(cls: type[TTSEngine]):
        _ENGINE_REGISTRY[name] = cls
        return cls
    return deco


def get_engine(
    name: Literal["kokoro", "piper"],
    **kwargs,
) -> TTSEngine:
    """Get an engine instance by name."""
    if name == "kokoro":
        return KokoroEngine(
            model_path=kwargs.get("model_path", Path.home() / ".cache/kokoro/kokoro-v1.0.onnx"),
            voices_path=kwargs.get("voices_path", Path.home() / ".cache/kokoro/voices-v1.0.bin"),
        )
    elif name == "piper":
        model_path = kwargs.get("model_path")
        if model_path is None:
            default_model = Path.home() / ".local/share/piper"
            if not any(default_model.rglob("*.onnx")):
                raise FileNotFoundError(
                    "Piper voice not found. Download one like this:\n"
                    "  python3 /home/jing/.local/lib/python3.12/site-packages/piper/download_voices.py en_US-lessac-medium --download-dir ~/.local/share/piper"
                )
            model_path = str(next(default_model.rglob("*.onnx")))
        return PiperEngine(
            model_path=model_path,
            config_path=kwargs.get("config_path"),
        )
    else:
        raise ValueError(f"Unknown engine: {name}. Available: {list(_ENGINE_REGISTRY.keys())}")


def list_engines() -> list[str]:
    return list(_ENGINE_REGISTRY.keys())
