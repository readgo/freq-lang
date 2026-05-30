# freqgen

CLI tool for generating `.freqpack` English learning courses with TTS.

## Features

- **Dual TTS engines**: Kokoro-ONNX + Piper, swappable via CLI
- **Extensible**: add new engines by implementing `TTSEngine`
- **Word-level timestamps**: each sentence has per-word timing for word-by-word replay
- **Batch import**: one sentence per line, outputs `.freqpack` zip

## Setup

```bash
# Install dependencies
pip install kokoro-onnx soundfile piper-tts click espeakng

# Download Kokoro models
mkdir -p ~/.cache/kokoro
wget -P ~/.cache/kokoro https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget -P ~/.cache/kokoro https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

# Install freqgen
pip install -e .
```

## Usage

```bash
# Single sentence
freqgen speak "Hello world" --voice af_sarah --engine kokoro

# Batch import
freqgen import sentences.txt --engine kokoro --voice af_sarah --output ./my-course

# Package into .freqpack
freqgen pack ./my-course -o my-course.freqpack

# List voices
freqgen voices --engine kokoro
```

## Architecture

- `engines/base.py` — `TTSEngine` abstract base
- `engines/kokoro.py` — Kokoro-ONNX implementation
- `engines/piper.py` — Piper implementation
- `engines/registry.py` — engine registration/factory
- `packager.py` — `.freqpack` zip builder
- `cli.py` — Click CLI entry point

## Output Format

`.freqpack` is a zip containing:
```
course.json   — sentences + word timestamps
meta.json     — title, language, engine, voice
audio/        — one .wav per sentence
```
