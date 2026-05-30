"""Kokoro-ONNX TTS engine."""

import re
import subprocess
from pathlib import Path

try:
    import soundfile as sf
    from kokoro_onnx import Kokoro
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

from .base import (
    GenerationResult,
    SentenceResult,
    TTSEngine,
    WordTimestamp,
    GenerationResultWithTimestamps,
)


# Kokoro voices: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
KOKORO_VOICES = [
    "af_sarah", "af_nicole", "af_sonia", "af_reese", "af_liam",
    "am_michael", "am_michael_2", "am_adam", "am_michael_neutral",
    "bf_emma", "bf_ella", "bf_isabella", "bf_lily",
    "bm_george", "bm_lewis",
    "bf_rare_1", "bf_rare_2",
]


class KokoroEngine(TTSEngine):
    name = "kokoro"
    default_voice = "af_sarah"
    available_voices = KOKORO_VOICES

    def __init__(self, model_path: str | Path, voices_path: str | Path):
        if not KOKORO_AVAILABLE:
            raise ImportError("kokoro-onnx not installed: pip install kokoro-onnx soundfile")
        self.model_path = Path(model_path)
        self.voices_path = Path(voices_path)
        self._kokoro = Kokoro(str(model_path), str(voices_path))

    def generate(self, text: str, voice: str, output_path: Path) -> GenerationResult:
        samples, sr = self._kokoro.create(text, voice=voice, speed=1.0)
        sf.write(str(output_path), samples, sr)
        duration = len(samples) / sr
        return GenerationResult(audio_path=output_path, duration_s=duration, sample_rate=sr)

    def generate_with_timestamps(self, text: str, voice: str, output_path: Path) -> SentenceResult:
        # Step 1: Generate audio
        samples, sr = self._kokoro.create(text, voice=voice, speed=1.0)
        sf.write(str(output_path), samples, sr)
        duration = len(samples) / sr

        # Step 2: Get phonemes from espeak-ng (Kokoro uses espeak-ng as g2p backend)
        phonemes = self._get_phonemes(text)
        wordimestamps = self._align_words_to_audio(text, phonemes, duration, sr, samples)

        return SentenceResult(
            text=text,
            audio_path=output_path,
            duration_s=duration,
            sample_rate=sr,
            words=wordimestamps,
        )

    def _get_phonemes(self, text: str) -> list[tuple[str, float]]:
        """Get phoneme sequence with estimated durations via espeak-ng."""
        # espeak-ng -x outputs: "w-er-d 'w 3ː d"
        # espeak-ng --ipa -q -x gives phonemes with duration info
        try:
            result = subprocess.run(
                ["espeak-ng", "--ipa", "-q", "-x", text],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
            # Parse phonemes from output (format: w@ - ld)
            raw = result.stdout.strip()
            # Phonemes separated by spaces, some have stress markers '
            phoneme_list = raw.split()
            # Estimate duration per phoneme (average ~60ms for English)
            avg_duration = 0.060
            result_list = []
            for ph in phoneme_list:
                if ph.strip():
                    result_list.append((ph.strip(), avg_duration))
            return result_list
        except Exception:
            return []

    def _align_words_to_audio(self, text: str, phonemes: list[tuple[str, float]],
                               duration: float, sr: int, samples) -> list[WordTimestamp]:
        """Align words to audio using phoneme count ratio."""
        if not phonemes:
            # Fallback: return single word with full duration
            return [WordTimestamp(word=text.strip(), start_s=0.0, end_s=duration)]

        # Split text into words
        words = text.replace(".", " . ").replace(",", " , ").replace("?", " ?").replace("!", " !").split()
        total_phonemes = len(phonemes)
        if total_phonemes == 0:
            return [WordTimestamp(word=text.strip(), start_s=0.0, end_s=duration)]

        # Count phonemes per word (heuristic: each word has proportional phonemes)
        word_phoneme_counts = []
        phoneme_idx = 0
        for word in words:
            # Approximate phoneme count from word length
            # This is rough - proper alignment needs montreal-forced-aligner or similar
            approx = max(1, len(word) * 2)
            word_phoneme_counts.append(approx)

        total_approx = sum(word_phoneme_counts)
        timestamps = []
        current_time = 0.0

        for i, word in enumerate(words):
            if word in (".", ",", "?", "!"):
                # Punctuation: small time step, include in previous or next
                continue
            phoneme_share = word_phoneme_counts[i] / total_approx
            word_duration = duration * phoneme_share
            end_time = min(current_time + word_duration, duration)
            timestamps.append(WordTimestamp(
                word=word,
                start_s=round(current_time, 3),
                end_s=round(end_time, 3),
            ))
            current_time = end_time

        # If we have fewer words than phonemes allow, fill remaining time
        if timestamps and current_time < duration:
            timestamps[-1] = WordTimestamp(
                word=timestamps[-1].word,
                start_s=timestamps[-1].start_s,
                end_s=duration,
            )

        return timestamps
