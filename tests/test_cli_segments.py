"""Test cli.py segment generation: segment display keeps original numbers,
TTS audio is generated from per-segment number-to-words conversion."""

import json
import zipfile
from pathlib import Path

from click.testing import CliRunner

from src.freqgen.cli import main
from src.freqgen.engines.base import GenerationResult


class FakeEngine:
    """Minimal TTS engine stub: records input text, writes a fake wav."""

    name = "fake"
    default_voice = "af_sarah"
    available_voices = ["af_sarah"]

    def __init__(self):
        self.calls = []  # (text, output_path_str)

    def generate(self, text, voice, output_path):
        output_path = Path(output_path)
        output_path.write_bytes(b"RIFF----WAVE fake")
        self.calls.append((text, str(output_path)))
        return GenerationResult(audio_path=output_path, duration_s=1.0)

    def voices(self):
        return self.available_voices


def _run_pack(monkeypatch, tmp_path, text, splitter="phrasplit"):
    txt = tmp_path / "course.txt"
    txt.write_text(text, encoding="utf-8")
    engine = FakeEngine()
    import src.freqgen.cli as cli_mod
    monkeypatch.setattr(cli_mod, "get_engine", lambda *a, **k: engine)
    out = tmp_path / "out.freqpack"
    runner = CliRunner()
    result = runner.invoke(
        main, [str(txt), "-o", str(out), "-v", "af_sarah", "-e", "kokoro", "-s", splitter]
    )
    assert result.exit_code == 0, result.output
    with zipfile.ZipFile(out) as zf:
        course = json.loads(zf.read("course.json"))
    return course, engine


def test_segments_keep_original_numbers(monkeypatch, tmp_path):
    """Display/tts split counts differ (4 vs 6): segments must still show
    original numbers, while TTS audio uses converted words."""
    sent = (
        "The Do Hiemon Box went on sale in April for 1.5 million yen "
        "(around  $9,200), but they are also available to rent at "
        "300,000 yen ($1,800) a month."
    )
    course, engine = _run_pack(monkeypatch, tmp_path, sent)

    target = next(s for s in course["sentences"] if "1.5 million" in s["text"])
    assert target["text"] == sent  # sentence-level text keeps original

    seg_texts = [seg["text"] for seg in target["segments"]]
    assert len(seg_texts) > 1

    # Segment display keeps original numbers
    assert any("1.5 million" in t for t in seg_texts)
    assert any("$9,200" in t for t in seg_texts)
    assert any("300,000" in t for t in seg_texts)
    assert any("$1,800" in t for t in seg_texts)

    # Segment display must NOT contain TTS-converted words
    assert not any("one point five" in t for t in seg_texts)
    assert not any("nine thousand" in t for t in seg_texts)
    assert not any("three hundred thousand" in t for t in seg_texts)

    # TTS audio text uses converted words
    tts_texts = [c[0] for c in engine.calls]
    assert any("one point five million" in t for t in tts_texts)
    assert any("nine thousand two hundred dollars" in t for t in tts_texts)
    assert any("three hundred thousand yen" in t for t in tts_texts)
    assert any("one thousand eight hundred dollars" in t for t in tts_texts)


def test_segments_simple_sentence(monkeypatch, tmp_path):
    """No numbers: display and tts identical."""
    sent = "This is just a plain sentence without any numbers inside it."
    course, engine = _run_pack(monkeypatch, tmp_path, sent)

    target = course["sentences"][0]
    assert target["text"] == sent
    segs = target.get("segments", [])
    for seg in segs:
        assert seg["text"] in sent  # segments are substrings of original
