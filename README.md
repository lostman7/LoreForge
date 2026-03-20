# LoreForge

LoreForge is a desktop RPG chat client for talking to AI characters with persistent lore, memory, portraits, backgrounds, music, speech input, and speech output.

## What is active in this repo?

The **current app logic** lives in the Python/PyQt code under `src/`.

- Launch entry point: `src/main.py`
- Main chat window: `src/ui/main_window.py`
- TTS / STT logic: `src/audio/`
- Character data: `knowledge/`
- Offline Qwen3-TTS model folders: `models/`

This repo also contains Electron packaging/frontend files (`main.js`, `index.html`, `renderer.js`, `preload.js`, `style.css`), but the chat-room code you asked me to wire up is the Python desktop app under `src/`.

## Features

- Multi-backend AI chat through the providers configured in `config.json`
- Character folders with portraits, backgrounds, lore, and optional music
- Local/offline **Qwen3-TTS character speech** using downloaded model files
- Optional Piper / system / cloud TTS paths already present in the codebase
- Sidebar speech controls for:
  - `TTS`
  - `STT`
  - `Character Speech` (offline Qwen3-TTS voice cloning)
- Per-character voice cloning using:
  - `voice_reference.wav`
  - `voice_reference.txt`
- Persistent memory / RAG files under each character folder
- Rich hero persona creation with titles, pronouns, motivations, traits, and specialties
- Placeholder Adventure Board content for guild quests and arena challengers

## Repository structure

```text
LoreForge/
├── config.json                  # Main app configuration
├── assets/game/                 # Placeholder quest board + arena roster content
├── requirements.txt             # Python dependencies
├── README.md                    # Main setup and usage guide
├── architecture.md              # Architecture notes
├── models/                      # Offline Qwen3-TTS model folders
│   └── README.md                # Quick Qwen model notes
├── knowledge/                   # Character folders
│   └── <CharacterName>/
│       ├── profile.txt
│       ├── config.json
│       ├── avatar.png
│       ├── background.png
│       ├── <CharacterName>.mp3          # optional ambient music
│       ├── voice_reference.wav          # optional Qwen clone reference audio
│       ├── voice_reference.txt          # optional transcript for the reference audio
│       ├── Background/
│       │   └── backstory.mp3            # optional backstory audio
│       ├── Documents/                   # optional extra lore docs
│       ├── rag/
│       │   └── character_data.txt
│       └── voice/
│           ├── local/                   # optional local voice assets (ex: Piper)
│           └── cloud/                   # optional cloud voice config
└── src/
    ├── main.py
    ├── ai/
    ├── audio/
    ├── memory/
    ├── presets/
    ├── session_logging/
    └── ui/
```

## Python requirements

Install the Python dependencies first:

```bash
pip install -r requirements.txt
```

Important runtime packages already listed there:

- `PyQt6`
- `speechrecognition`
- `pyaudio`
- `torch`
- `transformers`
- `soundfile`
- `qwen-tts`
- `playsound`
- `pyttsx3`

### System dependencies you may still need

Depending on your OS, you may also need:

- **PortAudio / PyAudio** support for microphone capture
- A local audio playback utility such as **ffplay** or **aplay**
- GPU drivers / CUDA if you want faster local Qwen inference

If STT will not start, the most common cause is missing microphone / PyAudio support.
If TTS generates audio but nothing plays, the most common cause is missing local playback tools.

## Running the app

### Python desktop app

```bash
python3 -m src.main
```

You can also run:

```bash
python3 src/main.py
```

### Electron shell / packaging files

If you are using the Electron side of the repo as well:

```bash
npm install
npm start
```

## Offline Qwen3-TTS setup

LoreForge now supports **offline/local Qwen3-TTS character speech**.

### What LoreForge expects by default

The app looks for these paths in `config.json`:

```json
"tts": {
  "qwen3_model_path": "./models/Qwen3-TTS-12Hz-0.6B-Base",
  "qwen3_tokenizer_path": "./models/Qwen3-TTS-Tokenizer-12Hz"
}
```

### Download the model files

The official Qwen3-TTS repo documents these download commands.

#### Hugging Face CLI

```bash
huggingface-cli download Qwen/Qwen3-TTS-Tokenizer-12Hz --local-dir ./models/Qwen3-TTS-Tokenizer-12Hz
huggingface-cli download Qwen/Qwen3-TTS-12Hz-0.6B-Base --local-dir ./models/Qwen3-TTS-12Hz-0.6B-Base
```

#### ModelScope

```bash
modelscope download --model Qwen/Qwen3-TTS-Tokenizer-12Hz --local_dir ./models/Qwen3-TTS-Tokenizer-12Hz
modelscope download --model Qwen/Qwen3-TTS-12Hz-0.6B-Base --local_dir ./models/Qwen3-TTS-12Hz-0.6B-Base
```

### Character voice clone files

For per-character voice cloning, place these files in the character folder:

```text
knowledge/<CharacterName>/voice_reference.wav
knowledge/<CharacterName>/voice_reference.txt
```

LoreForge also checks these alternate locations:

```text
knowledge/<CharacterName>/voice/voice_reference.wav
knowledge/<CharacterName>/voice/voice_reference.txt
knowledge/<CharacterName>/voice/local/voice_reference.wav
knowledge/<CharacterName>/voice/local/voice_reference.txt
```

### What the files should contain

- `voice_reference.wav`: a clean sample of the target character voice
- `voice_reference.txt`: the exact spoken transcript of that WAV file

### Turning it on in the app

Inside the chat-room sidebar:

- Leave normal `TTS` on if you still want regular voice playback behavior
- Turn on **`Character Speech`** to force the selected character to speak using the local Qwen3-TTS setup

If the button refuses to stay on, LoreForge is usually missing one of these:

- `qwen-tts`
- `soundfile`
- local Qwen model files in `models/`
- `voice_reference.wav`
- `voice_reference.txt`

## STT setup

LoreForge currently supports microphone capture through `speech_recognition`.

### Current STT config fields

From `config.json`:

```json
"stt": {
  "engine": "google",
  "language": "en-US",
  "timeout": 5,
  "phrase_limit": 10,
  "ambient_noise_duration": 0.8,
  "pause_threshold": 0.8,
  "non_speaking_duration": 0.5,
  "openai_model": "whisper-1"
}
```

### STT engines currently exposed in the UI

- `google`
- `openai`
- `whisper`
- `huggingface`
- `system`

### Important note about STT

- **Microphone capture is local**.
- **Google STT is not offline**.
- **OpenAI / Whisper API transcription is not offline** and needs an API key in `config.json`.

So if you want the app to stay fully offline, keep that in mind: **the new offline part is the Qwen3-TTS character speech path, not the current STT transcription backend**.

### Sidebar STT behavior

The STT toggle now does a startup check.
If microphone setup fails, the button flips back off instead of pretending STT started.

## Character folder guide

A good character folder looks like this:

```text
knowledge/
└── Mildred/
    ├── profile.txt
    ├── config.json
    ├── avatar.png
    ├── background.png
    ├── Mildred.mp3
    ├── voice_reference.wav
    ├── voice_reference.txt
    ├── Background/
    │   └── backstory.mp3
    ├── Documents/
    └── rag/
        └── character_data.txt
```

### Required files

Strictly speaking, the important ones are:

- `profile.txt`
- `config.json`

### Common optional files

- `avatar.png`
- `background.png`
- `<CharacterName>.mp3`
- `Background/backstory.mp3`
- `Documents/*`
- `rag/character_data.txt`
- `voice_reference.wav`
- `voice_reference.txt`

## Config guide

### TTS section

Important fields in `config.json`:

```json
"tts": {
  "engine": "piper",
  "fallback_to_system": true,
  "character_speech_enabled": false,
  "qwen3_model": "Qwen3-TTS-12Hz-0.6B-Base",
  "qwen3_model_path": "./models/Qwen3-TTS-12Hz-0.6B-Base",
  "qwen3_tokenizer_path": "./models/Qwen3-TTS-Tokenizer-12Hz",
  "qwen3_models_dir": "./models",
  "qwen3_language": "Auto",
  "qwen3_device": "auto",
  "qwen3_dtype": "auto"
}
```

### API section

Cloud features still use the `apis` block in `config.json`.
If you are staying completely offline, you can leave them blank.

## Troubleshooting

### Character Speech will not turn on

Check all of the following:

1. `pip install -r requirements.txt` completed successfully
2. `models/Qwen3-TTS-12Hz-0.6B-Base` exists
3. `models/Qwen3-TTS-Tokenizer-12Hz` exists
4. The selected character has `voice_reference.wav`
5. The selected character has `voice_reference.txt`

### STT button turns back off immediately

Usually one of these is missing:

- microphone permissions
- working input device
- `pyaudio`
- PortAudio system libraries

### No sound plays

Check:

- system volume
- output device
- local playback utilities such as `ffplay` / `aplay`
- whether fallback system TTS is enabled

### Qwen3 is too slow

Try:

- using GPU acceleration
- reducing other local workloads
- keeping the 0.6B base model instead of a larger model

## Notes

- Character data is stored under `knowledge/`, not `Presets/`.
- The README now describes the **current Python app structure** rather than older/legacy assumptions.
- `models/README.md` is still present as a shorter quick reference for the offline Qwen model folders.
