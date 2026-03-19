# LoreForge - Immersive AI RPG Companion

LoreForge is a modern, standalone Electron application designed for immersive roleplaying with AI characters. It features a premium, glassmorphic UI, high-quality voice-to-text, and deep character memory.

## 🚀 Key Features

- **🎮 Standalone RPG Experience**: Full-screen immersive mode with dynamic backgrounds and modern aesthetics.
- **🤖 Multi-Backend AI**: Seamlessly switch between **Claude**, **ChatGPT**, **Grok**, **Llama Cloud**, and local models via **Ollama**.
- **🎤 Advanced STT**: Integrated OpenAI Whisper support with real-time WebSocket streaming for live transcriptions.
- **🧠 Character Memory**: Each NPC has persistent memory and dedicated **RAG (Retrieval-Augmented Generation)** document indexing.
- **🎭 Character Creator**: Build new NPCs on the fly with custom lore, roles, and locations.
- **📚 Lore Folders**: Drop `.txt` or `.md` files into a character's `Documents/` folder to expand their knowledge instantly.

## 📦 Installation & Setup

### Prerequisites
- **Node.js 16+** (for the Electron frontend)
- **Python 3.10+** (for the AI/RAG sidecar)
- **Ollama** (optional, for local AI)

### Quick Start
1. **Clone the repository**
2. **Install Backend Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Frontend Dependencies:**
   ```bash
   npm install
   ```
4. **Launch the App:**
   ```bash
   npm start
   ```

## 🎯 Usage

### Immersive Chat
- Select a character from the sidebar to begin.
- Use **Ctrl+Enter** to send messages.
- Click **🎤 Start STT** to talk to your NPCs in real-time.

### Creating NPCs
- Use the **🎭 Create Character** button in the sidebar.
- Give them a name, role, and personality. LoreForge will automatically create their folder structure in `Presets/`.
- Add context by dropping files into `Presets/[Name]/Documents/` and clicking **📚 Index Documents**.

### AI Configuration
- Click **⚙️ AI & API Keys** to configure your favorite AI providers.
- Supports **OpenAI API**, **Anthropic (Claude)**, **xAI (Grok)**, **Llama Cloud**, and **LM Studio**.

## 🛠️ Development & Distribution

### Project Structure
- `main.js`: Electron main process (manages window & Python sidecar).
- `src/server.py`: FastAPI backend handling AI, RAG, and STT.
- `renderer.js` / `index.html`: Modern web frontend.
- `Presets/`: Character data and lore folders.

### Building Standalone Executables
LoreForge uses `electron-builder` to create installers for Windows, Linux, and macOS.

```bash
# Build for current platform
npm run build
```

## 🤝 Acknowledgments
- **Meta Llama**: Powerful open-source AI.
- **Claude & OpenAI**: World-class AI reasoning.
- **Whisper**: Industry-leading STT.
- **FastAPI**: High-performance backend sidecar.
- **Electron**: Premium desktop experience.

---
**Ready for your next adventure? Start LoreForge and build your world!**
*: Local AI model hosting
- **Piper**: High-quality local TTS
- **ChromaDB**: Vector database for RAG
- **PyQt6**: Cross-platform GUI framework
- **ElevenLabs**: Cloud TTS service

---

## 🎨 Asset Guidelines

To ensure a premium and consistent experience across all characters, please follow these standards:

### 🏞️ Background Images
- **Resolution**: **1536 × 1024 pixels**.
- **Consistency**: All chatroom backgrounds must be this size to ensure proper alignment and rendering.
- **Placement**: Upload via the Character Creator or place in `knowledge/[CharacterName]/background.png`.

### 🎵 Background Music
- **Format**: `.mp3`.
- **Naming**: Music files should be named exactly like the character's folder: `knowledge/[CharacterName]/[CharacterName].mp3`.
- **Volume**: Music is automatically capped at **35% volume** to provide a subtle ambient atmosphere.
- **Placement**: Upload via the Character Creator or drop the file directly into the NPC's folder.

---

**Ready to start your RPG adventure? Run `python setup_and_run.py` and begin chatting with AI characters!**