"""freqgen CLI — single-entry: freqgen sentences.txt [--voice af_sarah] [--engine kokoro]"""

import sys
from pathlib import Path

import click

from .engines import get_engine
from .engines.base import GenerationResult
from .packager import FreqpackPackager
from .splitters import get_splitter
from .text_processor import preprocess_for_tts, clean_display_text


@click.command()
@click.version_option(version="0.1.0")
@click.argument("input", nargs=1)
@click.option("-o", "--output", "output_path", default=None,
              help="Output path (file.freqpack for import, .wav for single text)")
@click.option("-v", "--voice", default=None,
              help="Voice name (default: engine's first available voice)")
@click.option("-e", "--engine", default="kokoro", help="TTS engine (kokoro/piper)")
def main(input: str, output_path: str, voice: str | None, engine: str):
    """freqgen — generate .freqpack English learning courses with TTS.

    Usage:
      freqgen sentences.txt                 import + pack → sentences.freqpack
      freqgen "Hello world"                 speak single sentence → stdout.wav
      freqgen sentences.txt -o my.zip       import + pack → my.zip
      freqgen "Hello" -o out.wav           speak → out.wav
      freqgen voices                        list available voices
      freqgen example/                      batch: convert all .txt in directory
    """
    input = input.strip()

    if input == "voices":
        _list_voices(engine)
        return

    input_path = Path(input)

    if input_path.is_dir():
        _batch_import(input_path, output_path, voice, engine)
    elif input_path.exists() and input_path.is_file():
        _import_and_pack(input_path, output_path, voice, engine)
    elif not input_path.exists():
        _speak(input, voice, engine, output_path)
    else:
        click.echo(f"Not a file: {input}", err=True)
        sys.exit(1)


def _resolve_voice(eng, voice: str | None) -> str:
    """Return voice name, using engine default if not specified or not in engine's voices."""
    if voice is None:
        return eng.voices()[0]
    if voice in eng.voices():
        return voice
    default = eng.voices()[0]
    click.echo(f"Unknown voice '{voice}'. Using engine default: {default}", err=True)
    return default


def _speak(text: str, voice: str | None, engine: str, output_path: str | None):
    try:
        eng = get_engine(engine)
    except ImportError as e:
        click.echo(f"Missing dependency: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to load engine '{engine}': {e}", err=True)
        sys.exit(1)

    voice = _resolve_voice(eng, voice)
    out = Path(output_path) if output_path else Path("stdout.wav")
    try:
        result = eng.generate(text, voice=voice, output_path=out)
        click.echo(f"Generated: {out} ({result.duration_s:.2f}s)")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _import_and_pack(input_path: Path, output_path: str | None,
                    voice: str | None, engine: str,
                    output_dir_override: Path | None = None,
                    freqpack_dir_override: Path | None = None):
    """Convert a .txt file to .freqpack."""
    with open(input_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]
    if not sentences:
        click.echo("No sentences found.", err=True)
        sys.exit(1)

    course_name = input_path.stem

    if output_dir_override:
        output_dir = output_dir_override
        output_dir.mkdir(parents=True, exist_ok=True)
        freqpack_dir = freqpack_dir_override or output_dir / "courses"
        freqpack_dir.mkdir(parents=True, exist_ok=True)
        freqpack_path = freqpack_dir / f"{course_name}.freqpack"
    else:
        output_dir = Path("output") / course_name
        output_dir.mkdir(parents=True, exist_ok=True)
        if output_path:
            freqpack_path = Path(output_path)
        else:
            freqpack_path = output_dir.parent / f"{course_name}.freqpack"

    try:
        eng = get_engine(engine)
    except Exception as e:
        click.echo(f"Failed to load engine '{engine}': {e}", err=True)
        sys.exit(1)

    voice = _resolve_voice(eng, voice)
    packager = FreqpackPackager(output_dir, title=course_name, engine=engine, voice=voice)

    # Sentence splitter (phrasplit)
    try:
        splitter = get_splitter("phrasplit")
    except Exception as e:
        click.echo(f"Warning: splitter unavailable ({e}), skipping sentence split", err=True)
        splitter = None

    click.echo(f"Processing {len(sentences)} sentences with {engine} ({voice})...")

    for i, sent in enumerate(sentences):
        wav_path = output_dir / "audio" / f"sent_{i:04d}.wav"
        wav_path.parent.mkdir(parents=True, exist_ok=True)

        # Preprocess: prn markers + number-to-words
        display_sent = clean_display_text(sent)
        tts_sent = preprocess_for_tts(sent)
        log_sent = display_sent[:60]

        # Generate full sentence TTS (using processed text)
        try:
            result = eng.generate(tts_sent, voice=voice, output_path=wav_path)
        except Exception as e:
            click.echo(f"  [ERROR] [{i+1}] {log_sent}: {e}", err=True)
            continue

        # Split sentence if splitter available (split on TTS text)
        segments: list[GenerationResult] = []
        segment_texts: list[str] = []
        if splitter:
            short_texts = splitter.split(tts_sent)
            if len(short_texts) > 1:
                click.echo(f"  [{i+1}/{len(sentences)}] split into {len(short_texts)} parts")
                for seg_idx, seg_text in enumerate(short_texts):
                    seg_path = output_dir / "audio" / f"sent_{i:04d}_{seg_idx:02d}.wav"
                    try:
                        seg_result = eng.generate(seg_text, voice=voice, output_path=seg_path)
                        segments.append(seg_result)
                        segment_texts.append(seg_text)
                    except Exception as e:
                        click.echo(f"  [SEGMENT ERROR] {seg_text[:40]}: {e}", err=True)
                        break

        # Store display text in course.json, use preprocessed text for TTS segments
        packager.add_sentence(result, i, text=display_sent,
                              segments=segments if segments else None,
                              segment_texts=segment_texts if segment_texts else None)

        click.echo(f"  [{i+1}/{len(sentences)}] {log_sent}")

    packager.write()

    try:
        packed = packager.package(freqpack_path)
        click.echo(f"Done: {packed}")
    except Exception as e:
        click.echo(f"Packaging error: {e}", err=True)
        sys.exit(1)


def _batch_import(input_dir: Path, output_path: str | None, voice: str | None, engine: str):
    """Convert all .txt files in a directory to .freqpack."""
    txt_files = sorted(input_dir.rglob("*.txt"))
    if not txt_files:
        click.echo(f"No .txt files found in {input_dir}", err=True)
        sys.exit(1)

    batch_root = Path("output") / input_dir.name
    courses_dir = batch_root / f"{input_dir.name}_courses"
    courses_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Found {len(txt_files)} .txt file(s) in {input_dir}/\n")

    for txt_file in txt_files:
        parent_rel = txt_file.parent.relative_to(input_dir)
        rel_dir_parts = parent_rel.parts

        if not rel_dir_parts:
            out_dir = batch_root / txt_file.stem
        else:
            out_dir = batch_root / Path(*rel_dir_parts) / txt_file.stem

        click.echo(f"--- Processing: {txt_file.name} ---")
        _import_and_pack(txt_file, None, voice, engine,
                         output_dir_override=out_dir,
                         freqpack_dir_override=courses_dir)
        click.echo()

    click.echo(f"Batch complete: {len(txt_files)} course(s) created in output/{input_dir.name}/")


def _list_voices(engine: str):
    try:
        eng = get_engine(engine)
        click.echo(f"Engine: {eng.name}")
        for v in eng.voices():
            click.echo(f"  {v}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
