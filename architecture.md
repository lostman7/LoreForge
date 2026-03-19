# LoreForge Architecture Design

## Overview
LoreForge is a cross-platform desktop application for immersive RPG/AI chat interactions. Built with Python for flexibility and cross-platform support.

## Technology Stack
- **UI Framework**: PyQt6 - Cross-platform, modern UI with theming support
- **AI Backend**: Ollama - Local model hosting with GPU acceleration
- **TTS Engine**: Piper - Local, high-quality TTS with voice cloning support
- **STT Engine**: speech_recognition (with PyAudio) - Cross-platform speech input
- **Vector Database**: ChromaDB - Lightweight RAG memory storage
- **Embeddings**: sentence-transformers - For memory retrieval
- **Packaging**: PyInstaller - Cross-platform executable generation

## Core Components

### 1. Main Application (main.py)
- Entry point
- Initializes PyQt6 application
- Loads configuration
- Creates main window

### 2. User Interface (src/ui/)
- **MainWindow**: Central chat interface
  - Chat display area with scrollable bubbles
  - Message input field
  - Preset selection dropdown
  - Dynamic background display
  - Avatar display area
- **ChatBubble**: Custom widget for messages with avatar support
- **ThemeManager**: Handles dark mode and accent colors

### 3. Preset System (src/presets/)
- **PresetManager**: Loads and manages character presets
- **Preset**: Data class for character configuration
  - profile.txt: Personality and backstory
  - avatar.png: Character image
  - background.png: Chat background
  - voice/: Piper voice model files
  - config.json: Behavior flags and paths

### 4. Audio System (src/audio/)
- **TTSManager**: Handles text-to-speech
  - Local Piper integration
  - Optional ElevenLabs API support
  - Voice file management
- **STTManager**: Speech-to-text input
  - Microphone capture
  - Real-time transcription

### 5. Memory System (src/memory/)
- **MemoryManager**: Floating memory and RAG
  - RAM/VRAM storage for quick access
  - ChromaDB for persistent vector storage
  - Session summary loading
- **RAGRetriever**: Context retrieval for AI prompts

### 6. AI Integration (src/ai/)
- **AIModel**: Abstract interface for AI backends
- **OllamaClient**: Local model integration
- **PromptBuilder**: Constructs roleplay prompts with memory context

### 7. Logging System (src/logging/)
- **SessionLogger**: Manages chat session logs
- **LogSummarizer**: Creates summarized session logs
- Folder structure: Logs/CharacterName/session_XXX.txt

## Data Flow
1. User selects preset → PresetManager loads assets and config
2. UI updates background, avatar, voice settings
3. MemoryManager loads character memory and logs
4. User inputs message (text/voice) → STT converts if needed
5. PromptBuilder creates AI prompt with context
6. AI generates response
7. TTS plays response audio
8. Response displayed in chat with avatar
9. SessionLogger records summarized interaction

## File Structure
```
LoreForge/
├── main.py
├── requirements.txt
├── pyrightconfig.json
├── architecture.md
├── Presets/
│   └── ExampleNPC/
│       ├── profile.txt
│       ├── avatar.png
│       ├── background.png
│       ├── voice/
│       │   └── en_US-lessac-medium.onnx
│       └── config.json
├── Logs/
│   └── ExampleNPC/
│       └── session_001.txt
└── src/
    ├── __init__.py
    ├── ui/
    │   ├── main_window.py
    │   ├── chat_bubble.py
    │   └── theme_manager.py
    ├── presets/
    │   ├── preset_manager.py
    │   └── preset.py
    ├── audio/
    │   ├── tts_manager.py
    │   └── stt_manager.py
    ├── memory/
    │   ├── memory_manager.py
    │   └── rag_retriever.py
    ├── ai/
    │   ├── ai_model.py
    │   ├── ollama_client.py
    │   └── prompt_builder.py
    └── logging/
        ├── session_logger.py
        └── log_summarizer.py
```

## Cross-Platform Considerations
- **Linux**: Native support via PyQt6, Piper (Vulkan/OpenCL)
- **Windows**: PyQt6 wheels, Piper executable
- **GPU Support**: Ollama handles AMD/NVIDIA acceleration
- **Audio**: PyAudio for cross-platform audio I/O

## Performance Optimizations
- Lazy loading of presets
- Memory pooling for floating memory
- Asynchronous TTS/STT processing
- Vector quantization for memory efficiency

## Security Considerations
- Local-only operation (no cloud required)
- API keys stored securely for optional cloud TTS
- No external data transmission without user consent