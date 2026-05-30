"""TTS Engine abstract base."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class GenerationResult:
    audio_path: Path
    duration_s: float
    sample_rate: int = 24000


@dataclass
class WordTimestamp:
    word: str
    start_s: float
    end_s: float


@dataclass
class SentenceResult:
    text: str
    audio_path: Path
    duration_s: float
    sample_rate: int = 24000
    words: list[WordTimestamp] | None = None


@dataclass
class GenerationResultWithTimestamps:
    sentences: list[SentenceResult]


class TTSEngine(ABC):
    """Abstract TTS engine."""

    name: str = "unknown"
    default_voice: str = ""
    available_voices: list[str] = []

    @abstractmethod
    def generate(self, text: str, voice: str, output_path: Path) -> GenerationResult:
        """Generate single audio file."""
        ...

    @abstractmethod
    def generate_with_timestamps(self, text: str, voice: str, output_path: Path) -> SentenceResult:
        """Generate audio with word-level timestamps for word-by-word replay."""
        ...

    def voices(self) -> list[str]:
        """Return available voices."""
        return self.available_voices
