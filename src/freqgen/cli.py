"""freqgen CLI — single-entry: freqgen sentences.txt [--voice af_sarah] [--engine kokoro]"""

import sys
import json
from pathlib import Path

import click

from .engines import get_engine
from .packager import FreqpackPackager


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
    """
    input = input.strip()

    if input == "voices":
        _list_voices(engine)
        return

    input_path = Path(input)

    if input_path.exists() and input_path.is_file():
        _import_and_pack(input_path, output_path, voice, engine)
    elif input_path.exists() and not input_path.is_file():
        click.echo(f"Not a file: {input}", err=True)
        sys.exit(1)
    else:
        _speak(input, voice, engine, output_path)


def _resolve_voice(eng, voice: str | None) -> str:
    """Return voice name, using engine default if not specified or not in engine's voices."""
    if voice is None:
        return eng.voices()[0]
    if voice in eng.voices():
        return voice
    # Unknown voice — offer engine's own default instead of crashing
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


def _import_and_pack(input_path: Path, output_path: str | None, voice: str | None, engine: str):
    with open(input_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]
    if not sentences:
        click.echo("No sentences found.", err=True)
        sys.exit(1)

    course_name = input_path.stem
    output_dir = Path("output") / course_name
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_path:
        freqpack_path = Path(output_path)
    else:
        freqpack_path = Path("output") / f"{course_name}.freqpack"

    try:
        eng = get_engine(engine)
    except Exception as e:
        click.echo(f"Failed to load engine '{engine}': {e}", err=True)
        sys.exit(1)

    voice = _resolve_voice(eng, voice)

    packager = FreqpackPackager(output_dir, title=course_name, engine=engine, voice=voice)

    click.echo(f"Processing {len(sentences)} sentences with {engine} ({voice})...")

    for i, sent in enumerate(sentences):
        wav_path = output_dir / "audio" / f"sent_{i:04d}.wav"
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = eng.generate_with_timestamps(sent, voice=voice, output_path=wav_path)
            packager.add_sentence(result, i)
            click.echo(f"  [{i+1}/{len(sentences)}] {sent[:60]}")
        except Exception as e:
            click.echo(f"  [ERROR] [{i+1}] {sent[:60]}: {e}", err=True)

    packager.write()

    try:
        packed = packager.package(freqpack_path)
        click.echo(f"Done: {packed}")
    except Exception as e:
        click.echo(f"Packaging error: {e}", err=True)
        sys.exit(1)


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
