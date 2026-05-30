"""TTS abstract interface"""
from abc import ABC, abstractmethod
from pathlib import Path


class TTSProviderError(Exception):
    """Base exception for TTS provider issues"""
    pass


class BaseTTS(ABC):
    """Abstract TTS interface — all implementations inherit this"""

    @abstractmethod
    def synthesize(self, text: str, output: Path) -> None:
        """Convert text to speech, write to output file"""
        ...

    @classmethod
    def provider_name(cls) -> str:
        """Lowercase identifier used in TTS_PROVIDER env var"""
        return cls.__name__.lower().rstrip("tts").rstrip("TTS")

    @staticmethod
    def is_available() -> bool:
        """Return True if this provider can be used (dependencies present, etc.)"""
        return True
