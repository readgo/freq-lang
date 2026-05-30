"""freqgen CLI."""

import sys
from pathlib import Path

import click

from .engines import get_engine
from .engines.base import TTSEngine
from .packager import FreqpackPackager


@click.group()
@click.version_option(version="0.1.0")
def main():
    """freqgen — generate .freqpack English learning courses with TTS."""
    pass


@main.command()
@click.argument("text")
@click.option("--voice", default="af_sarah", help="Voice name")
@click.option("--engine", default="kokoro", help="TTS engine (kokoro/piper)")
@click.option("--output", "-o", default="output.wav", help="Output wav file")
def speak(text: str, voice: str, engine: str, output: str):
    """Generate audio for a single sentence."""
    try:
        eng = get_engine(engine)
        if voice not in eng.voices():
            click.echo(f"Unknown voice '{voice}'. Available: {eng.voices()[:5]}", err=True)
            sys.exit(1)
        result = eng.generate(text, voice=voice, output_path=Path(output))
        click.echo(f"Generated: {result.audio_path} ({result.duration_s:.2f}s)")
    except ImportError as e:
        click.echo(f"Missing dependency: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--engine", default="kokoro", help="TTS engine")
@click.option("--voice", default="af_sarah", help="Voice name")
@click.option("--output", "-o", default="course_out", help="Output directory")
@click.option("--title", default="My Course", help="Course title")
def import_cmd(input_file: str, engine: str, voice: str, output: str, title: str):
    """Import a text file (one sentence per line) and generate audio."""
    input_path = Path(input_file)
    output_dir = Path(output)

    try:
        eng = get_engine(engine)
    except Exception as e:
        click.echo(f"Failed to load engine: {e}", err=True)
        sys.exit(1)

    # Read sentences
    with open(input_path, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    if not sentences:
        click.echo("No sentences found.", err=True)
        sys.exit(1)

    packager = FreqpackPackager(output_dir, title=title, engine=engine, voice=voice)

    click.echo(f"Processing {len(sentences)} sentences with {engine}...")

    for i, sent in enumerate(sentences):
        wav_path = output_dir / "audio" / f"sent_{i:04d}.wav"
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = eng.generate_with_timestamps(sent, voice=voice, output_path=wav_path)
            packager.add_sentence(result, i)
            click.echo(f"  [{i+1}/{len(sentences)}] {sent[:60]}... -> {wav_path.name}")
        except Exception as e:
            click.echo(f"  [ERROR] Sentence {i}: {e}", err=True)

    packager.write()
    click.echo(f"\nDone. course.json + meta.json written to {output_dir}/")
    click.echo(f"Audio files: {(output_dir/'audio').glob('*.wav') and list((output_dir/'audio').glob('*.wav')).__len__()} files")


@main.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, help="Output .freqpack path")
def pack(input_dir: str, output: str):
    """Package a course directory into .freqpack."""
    output_path = Path(output)
    packager = FreqpackPackager(Path(input_dir))
    # Reconstruct from existing course.json
    course_file = Path(input_dir) / "course.json"
    if course_file.exists():
        import json
        with open(course_file) as f:
            data = json.load(f)
        # Just re-zip existing structure
        pass
    result = packager.package(output_path)
    click.echo(f"Packaged: {result}")


@main.command()
@click.option("--engine", default="kokoro", help="TTS engine")
def voices(engine: str):
    """List available voices for an engine."""
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
