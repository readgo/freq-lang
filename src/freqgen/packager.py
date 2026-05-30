"""Freqpack packager."""

import json
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from .engines.base import SentenceResult


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
class WordTimestampJSON:
    word: str
    start_s: float
    end_s: float

    def to_dict(self):
        return {"word": self.word, "start_s": self.start_s, "end_s": self.end_s}


@dataclass
class PauseRegionJSON:
    start_s: float
    end_s: float

    def to_dict(self):
        return {"start_s": self.start_s, "end_s": self.end_s}


@dataclass
class SentenceJSON:
    id: int
    text: str
    audio: str
    duration_s: float
    words: list[WordTimestampJSON]
    pauses: list[PauseRegionJSON]

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "audio": self.audio,
            "duration_s": self.duration_s,
            "words": [w.to_dict() for w in self.words],
            "pauses": [p.to_dict() for p in self.pauses],
        }


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

    def add_sentence(self, result: SentenceResult, index: int):
        words_json = []
        if result.words:
            for w in result.words:
                words_json.append(WordTimestampJSON(
                    word=w.word,
                    start_s=w.start_s,
                    end_s=w.end_s,
                ))

        pauses_json = []
        if result.pauses:
            for p in result.pauses:
                pauses_json.append(PauseRegionJSON(
                    start_s=p.start_s,
                    end_s=p.end_s,
                ))

        self.sentences.append(SentenceJSON(
            id=index,
            text=result.text,
            audio=f"audio/sent_{index:04d}.wav",
            duration_s=result.duration_s,
            words=words_json,
            pauses=pauses_json,
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
