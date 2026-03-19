# Offline Qwen3-TTS models

LoreForge can use a **local** Qwen3-TTS model for character speech.

## Recommended layout

Put the downloaded folders here:

```text
models/
├── Qwen3-TTS-12Hz-0.6B-Base/
└── Qwen3-TTS-Tokenizer-12Hz/
```

The app is configured by default to look for:

- `./models/Qwen3-TTS-12Hz-0.6B-Base`
- `./models/Qwen3-TTS-Tokenizer-12Hz`

## Official download commands

These commands come from the official Qwen3-TTS project.

### Hugging Face CLI

```bash
huggingface-cli download Qwen/Qwen3-TTS-12Hz-0.6B-Base --local-dir ./models/Qwen3-TTS-12Hz-0.6B-Base
huggingface-cli download Qwen/Qwen3-TTS-Tokenizer-12Hz --local-dir ./models/Qwen3-TTS-Tokenizer-12Hz
```

### ModelScope

```bash
modelscope download --model Qwen/Qwen3-TTS-12Hz-0.6B-Base --local_dir ./models/Qwen3-TTS-12Hz-0.6B-Base
modelscope download --model Qwen/Qwen3-TTS-Tokenizer-12Hz --local_dir ./models/Qwen3-TTS-Tokenizer-12Hz
```

## Per-character voice clone files

To give a character a cloned voice, add these files to the character folder in `knowledge/<CharacterName>/`:

- `voice_reference.wav`
- `voice_reference.txt`

Example:

```text
knowledge/
└── Mildred/
    ├── profile.txt
    ├── config.json
    ├── voice_reference.wav
    └── voice_reference.txt
```

When **Character Speech** is enabled in the sidebar, LoreForge will use those files with the local Qwen3-TTS base model for offline voice cloning.
