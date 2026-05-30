# freqgen

CLI tool for generating `.freqpack` English learning courses with TTS.

## Features

- **Dual TTS engines**: Kokoro-ONNX (default, best English quality) + Piper
- **Word-level timestamps**: each sentence has per-word timing for word-by-word replay
- **Single command**: auto-detects file import vs text-to-speech
- **Batch import**: one sentence per line, outputs `.freqpack` zip

## Setup

```bash
# Install dependencies
pip install kokoro-onnx soundfile piper-tts click espeakng

# Download Kokoro models
mkdir -p ~/.cache/kokoro
wget -P ~/.cache/kokoro https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
wget -P ~/.cache/kokoro https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

## Usage

```bash
# Batch import: generate .freqpack from sentence file
freqgen sentences.txt                     # → output/sentences.freqpack
freqgen sentences.txt -o my.freqpack       # custom output path
freqgen sentences.txt -e piper -v en_US-lessac-medium  # Piper engine

# Single sentence: generate .wav
freqgen "Hello world"                     # → stdout.wav
freqgen "Hello" -o hello.wav             # → hello.wav
freqgen "Hello" -v am_adam               # use a specific voice

# List available voices
freqgen voices                           # Kokoro voices (default)
freqgen voices -e piper                  # Piper voices (requires model setup)

# Pick a voice
freqgen "Hello" -v af_sarah             # Kokoro voice
```

## Voice Reference

### Kokoro (default, 54 voices)

| Prefix | Description |
|--------|-------------|
| `af_`  | American female |
| `am_`  | American male |
| `bf_`  | British female |
| `bm_`  | British male |

### Piper

Requires separate model download. See [piper-models](https://github.com/rmcpteam/piper-models).

## Output

`freqgen sentences.txt` writes to `output/` directory:

```
output/
├── sentences.freqpack      # zip archive
└── sentences/              # unpacked (also created during generation)
│   ├── course.json         # sentences + word timestamps
│   ├── meta.json           # title, language, engine, voice
│   └── audio/              # one .wav per sentence
```

## .freqpack Format

```json
{
  "title": "sentences",
  "language": "en",
  "engine": "kokoro",
  "voice": "af_sarah",
  "sentences": [
    {
      "id": 0,
      "text": "Kamakura Store Sells Kanji Ice Cream That Doesn't Melt",
      "audio": "audio/sent_0000.wav",
      "words": [
        { "word": "Kamakura", "start": 0.0, "end": 0.45 },
        { "word": "Store", "start": 0.45, "end": 0.72 },
        ...
      ]
    }
  ]
}
```

## Architecture

- `engines/base.py` — `TTSEngine` abstract base + data classes
- `engines/kokoro.py` — Kokoro-ONNX implementation
- `engines/piper.py` — Piper implementation
- `engines/registry.py` — engine registration/factory
- `packager.py` — `.freqpack` zip builder
- `cli.py` — Click CLI entry point
