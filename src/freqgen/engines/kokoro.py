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
    PauseRegion,
    SentenceResult,
    TTSEngine,
    WordTimestamp,
    GenerationResultWithTimestamps,
)


# Kokoro voices: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
KOKORO_VOICES = [
    "af_sarah", "af_nicole", "af_sonia", "af_reese", "af_liam",
    "am_michael", "am_michael_2", "am_adam", "am_mic...tral",
    "bf_emma", "bf_ella", "bf_isabella", "bf_lily",
    "bm_george", "bm_leon", "bf_rare_1", "bf_rare_2",
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
        samples, sr = self._kokoro.create(text, voice=voice, speed=1.0)
        sf.write(str(output_path), samples, sr)
        duration = len(samples) / sr

        phonemes = self._get_phonemes(text)
        words = self._align_words_to_audio(text, phonemes, duration, sr, samples)
        pauses = self._find_pauses(samples, sr)

        return SentenceResult(
            text=text,
            audio_path=output_path,
            duration_s=duration,
            sample_rate=sr,
            words=words,
            pauses=pauses,
        )

    def _get_phonemes(self, text: str) -> list[tuple[str, float]]:
        """Get phoneme sequence with estimated durations via espeak-ng."""
        try:
            result = subprocess.run(
                ["espeak-ng", "--ipa", "-q", "-x", text],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
            raw = result.stdout.strip()
            phoneme_list = raw.split()
            avg_duration = 0.060
            result_list = []
            for ph in phoneme_list:
                if ph.strip():
                    result_list.append((ph.strip(), avg_duration))
            return result_list
        except Exception:
            return []

    def _phoneme_count(self, word: str) -> int:
        """Count phoneme groups for a single word via espeak-ng -x."""
        try:
            result = subprocess.run(
                ["espeak-ng", "--ipa", "-q", "-x", word],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return 1
            return len([p for p in result.stdout.strip().split() if p.strip()])
        except Exception:
            return 1

    def _align_words_to_audio(self, text: str, phonemes: list[tuple[str, float]],
                               duration: float, sr: int, samples) -> list[WordTimestamp]:
        """Align words to audio using real phoneme counts per word from espeak-ng."""
        words = re.sub(r'[.,?!]', r' \g<0> ', text).split()
        word_phoneme_counts = []
        for word in words:
            if word in ('.', ',', '?', '!'):
                word_phoneme_counts.append(0)
            else:
                word_phoneme_counts.append(self._phoneme_count(word))

        valid_counts = [wc for i, wc in enumerate(word_phoneme_counts)
                       if words[i] not in ('.', ',', '?', '!')]
        total = sum(valid_counts)
        if total == 0:
            return [WordTimestamp(word=text.strip(), start_s=0.0, end_s=duration)]
        timestamps = []
        current_time = 0.0

        for i, word in enumerate(words):
            if word in ('.', ',', '?', '!'):
                continue
            share = word_phoneme_counts[i] / total
            word_duration = duration * share
            end_time = min(current_time + word_duration, duration)
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

    def _find_pauses(self, samples, sr: int) -> list[PauseRegion]:
        """Detect silence regions >= 100ms as potential phrase boundaries."""
        import numpy as np
        WINDOW = 0.020          # 20ms analysis window
        MIN_PAUSE = 0.100       # 100ms minimum silence to count as a pause
        THRESHOLD_RATIO = 0.08  # fraction of median energy to count as silence

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

        # Smooth over 3 windows to avoid transient spikes
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
