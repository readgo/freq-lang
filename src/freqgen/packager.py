"""Freqpack packager."""

import json
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from .engines.base import GenerationResult


@dataclass
class FreqpackMeta:
    title: str
    language: str = "en"
    version: str = "1.0"
    engine: str = ""
    voice: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SegmentJSON:
    text: str
    audio: str
    duration_s: float

    def to_dict(self):
        return {
            "text": self.text,
            "audio": self.audio,
            "duration_s": self.duration_s,
        }


@dataclass
class SentenceJSON:
    id: int
    text: str
    audio: str
    duration_s: float
    segments: list[SegmentJSON] = None

    def __post_init__(self):
        if self.segments is None:
            self.segments = []

    def to_dict(self):
        d = {
            "id": self.id,
            "text": self.text,
            "audio": self.audio,
            "duration_s": self.duration_s,
        }
        if self.segments:
            d["segments"] = [s.to_dict() for s in self.segments]
        return d


class FreqpackPackager:
    """Package generated audio into a .freqpack zip."""

    def __init__(self, output_dir: Path, title: str = "My Course",
                 engine: str = "", voice: str = ""):
        self.output_dir = Path(output_dir)
        self.audio_dir = self.output_dir / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.meta = FreqpackMeta(
            title=title,
            engine=engine,
            voice=voice,
        )
        self.sentences: list[SentenceJSON] = []

    def add_sentence(self, result: GenerationResult, index: int, text: str,
                     segments: list[GenerationResult] | None = None,
                     segment_texts: list[str] | None = None):
        """Add a sentence.

        Args:
            result: TTS result for the full sentence.
            index: Sentence index.
            text: Sentence text.
            segments: List of TTS results for each segment (optional).
            segment_texts: List of segment texts, aligned with segments.
        """
        segs: list[SegmentJSON] = []
        if segments and segment_texts:
            for seg_idx, (seg_result, seg_text) in enumerate(zip(segments, segment_texts)):
                segs.append(SegmentJSON(
                    text=seg_text,
                    audio=f"audio/sent_{index:04d}_{seg_idx:02d}.wav",
                    duration_s=seg_result.duration_s,
                ))

        self.sentences.append(SentenceJSON(
            id=index,
            text=text,
            audio=f"audio/sent_{index:04d}.wav",
            duration_s=result.duration_s,
            segments=segs,
        ))

    def write(self):
        course_data = {"sentences": [s.to_dict() for s in self.sentences]}
        meta_data = self.meta.to_dict()
        meta_data["created_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.output_dir / "course.json", "w", encoding="utf-8") as f:
            json.dump(course_data, f, ensure_ascii=False, indent=2)
        with open(self.output_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

    def package(self, output_path: Path):
        output_path = Path(output_path)
        if not output_path.name.endswith(".freqpack"):
            output_path = Path(str(output_path) + ".freqpack")
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(self.output_dir / "course.json", "course.json")
            zf.write(self.output_dir / "meta.json", "meta.json")
            for p in self.audio_dir.glob("*.wav"):
                zf.write(p, f"audio/{p.name}")
        return output_path
