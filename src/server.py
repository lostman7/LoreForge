from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Set
import os
import sys
import json
import base64
import asyncio
import logging
from pathlib import Path

# Suppress HuggingFace Hub warnings and logs
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# Add src to path for imports
base_dir = Path(__file__).parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from src.presets.preset_manager import PresetManager
from src.audio.stt_manager import STTManager
from src.memory.memory_manager import MemoryManager
from src.ai.ai_model import AIModel
from src.session_logging.session_logger import SessionLogger
from src.players.player_manager import PlayerManager

app = FastAPI(title="LoreForge API")

# Enable CORS for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
CONFIG_PATH = base_dir / 'config.json'
PERSONA_PATH = base_dir / 'persona.json'

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(new_config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(new_config, f, indent=2)

config = load_config()
preset_manager = PresetManager()
stt_manager = STTManager(config)
memory_manager = MemoryManager(config)
ai_model = AIModel(config)
session_logger = SessionLogger()
player_manager = PlayerManager()

# WebSocket connections for STT
stt_connections: Set[WebSocket] = set()

class PersonaStats(BaseModel):
    level: Optional[int] = 1
    strength: Optional[int] = 10
    dexterity: Optional[int] = 10
    intelligence: Optional[int] = 10
    charisma: Optional[int] = 10
    wisdom: Optional[int] = 10

class PersonaData(BaseModel):
    name: str
    backstory: Optional[str] = ""
    stats: Optional[PersonaStats] = None

class ChatRequest(BaseModel):
    message: str
    player: str
    weather: Optional[str] = None
    weather_prompt: Optional[str] = None
    persona: Optional[PersonaData] = None

class ChatResponse(BaseModel):
    response: str

class CharacterCreateRequest(BaseModel):
    name: str
    role: Optional[str] = ""
    location: Optional[str] = ""
    description: Optional[str] = ""
    voice_mode: Optional[str] = "local"
    avatar_image: Optional[str] = None
    background_image: Optional[str] = None
    music_data: Optional[str] = None
    rag_data: Optional[str] = None
    backstory_audio: Optional[str] = None

class PlayerPersonaCreateRequest(BaseModel):
    name: str
    backstory: Optional[str] = ""
    stats: Optional[Dict[str, Any]] = None
    avatar: Optional[str] = None

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    await websocket.accept()
    stt_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        stt_connections.remove(websocket)

async def stt_callback(text: str):
    """Callback triggered by STTManager when speech is recognized."""
    if not stt_connections:
        return
    
    # Broadcast to all connected clients (typically just one Electron window)
    for connection in list(stt_connections):
        try:
            await connection.send_json({"type": "stt_result", "text": text})
        except:
            stt_connections.remove(connection)

@app.get("/presets")
async def get_presets():
    preset_manager.refresh_presets() # Ensure we scan disk
    names = preset_manager.get_preset_names()
    results = []
    for name in names:
        preset = preset_manager.load_preset(name)
        if preset:
            results.append({
                "name": name,
                "character_name": preset.character_name,
                "avatar_path": preset.avatar_path,
                "job_title": preset.job_title,
                "location": preset.location
            })
    return results

@app.get("/presets/{name}")
async def get_preset(name: str):
    preset = preset_manager.load_preset(name)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    return {
        "name": name,
        "config": preset.config,
        "avatar_path": preset.avatar_path,
        "background_frames": preset.background_frames,
        "profile_text": preset.profile_text,
        "music_path": preset.music_path,
        "backstory_audio_path": preset.backstory_audio_path,
        "presets_dir": str(preset_manager.presets_dir) # Add this for frontend path construction if needed
    }

@app.get("/persona")
async def get_persona():
    if not PERSONA_PATH.exists():
        return {"name": "Traveler", "backstory": "", "stats": {}}
    with open(PERSONA_PATH, 'r') as f:
        return json.load(f)

@app.post("/persona")
async def save_persona(request: PersonaData):
    with open(PERSONA_PATH, 'w') as f:
        json.dump(request.dict(), f, indent=2)
    return {"status": "success"}

@app.post("/presets/refresh")
async def refresh_presets():
    preset_manager.refresh_presets()
    return {"status": "success", "message": "Presets refreshed"}

@app.get("/ai/models")
async def get_ai_models():
    """List available models for the current backend (primarily Ollama)."""
    backend = config.get('ai', {}).get('backend', 'ollama')
    
    if backend == 'ollama':
        try:
            import ollama
            models = ollama.list()
            # Standard Ollama response structure (v1.x) or pydantic response
            if isinstance(models, dict):
                return [m.get('model', m.get('name', 'unknown')) for m in models.get('models', [])]
            return [m.model if hasattr(m, 'model') else m.name for m in models.models]
        except Exception as e:
            print(f"Error listing Ollama models: {e}")
            return ["llama3.2:3b", "llama3.1:8b", "mistral"] # Fallback essentials
    
    # For others, return a list of common models
    if backend == 'openai':
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
    if backend == 'claude':
        return ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
        
    return []

@app.delete("/presets/{name}")
async def delete_preset(name: str):
    try:
        preset_manager.delete_preset(name)
        return {"status": "success", "message": f"Character {name} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/presets/create")
async def create_preset(request: CharacterCreateRequest):
    data = {
        "name": request.name,
        "role": request.role,
        "location": request.location,
        "description": request.description,
        "voice_mode": request.voice_mode,
    }

    # Handle base64 avatar image
    if request.avatar_image:
        data['avatar_base64'] = request.avatar_image

    # Handle base64 background image
    if request.background_image:
        data['background_base64'] = request.background_image

    # Handle base64 music file
    if request.music_data:
        data['music_base64'] = request.music_data

    # Handle base64 RAG data
    if request.rag_data:
        data['rag_base64'] = request.rag_data

    # Handle base64 backstory audio
    if request.backstory_audio:
        data['backstory_audio_base64'] = request.backstory_audio

    success = preset_manager.create_simple_preset(data)
    if success:
        return {"status": "success", "message": f"Character {request.name} created."}
    else:
        raise HTTPException(status_code=500, detail="Failed to create character.")

@app.post("/presets/{name}/chat", response_model=ChatResponse)
async def chat(name: str, request: ChatRequest):
    preset = preset_manager.load_preset(name)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    # Load memory
    memory_manager.load_preset_memory(name, request.player)
    
    # Construct prompt with context
    enhanced_message = f"Player {request.player} says: {request.message}"
    context = memory_manager.get_context(enhanced_message)
    
    # Build extra context for weather and persona
    extra_context = {}
    if request.weather_prompt:
        extra_context['weather_prompt'] = request.weather_prompt
    if request.persona:
        extra_context['persona'] = {
            'name': request.persona.name,
            'backstory': request.persona.backstory or '',
            'stats': request.persona.stats.dict() if request.persona.stats else {}
        }
    
    try:
        response_text = ai_model.generate_response(enhanced_message, context, preset, extra_context=extra_context)
        
        # Update memory
        memory_manager.add_interaction(enhanced_message, response_text)
        
        # Log session
        session_logger.start_session(name, request.player)
        session_logger.log_interaction(request.message, response_text, player=request.player)
        
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/presets/{name}/index")
async def index_documents(name: str):
    preset = preset_manager.load_preset(name)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
        
    # Correct path to character's local Documents folder in knowledge/
    doc_dir = preset_manager.presets_dir / name / "Documents"
    if not doc_dir.exists():
        doc_dir.mkdir(exist_ok=True)
        return {"status": "created", "message": f"Documents folder created at {doc_dir}. Add text files and try again."}
    
    # Trigger indexing
    memory_manager.load_preset_memory(name)
    count = memory_manager.index_character_documents(name, doc_dir)
    
    return {"status": "success", "message": f"Indexed {count} files from {doc_dir}"}

@app.get("/config")
async def get_config():
    return load_config()

@app.post("/config/update")
@app.post("/config") # Support both paths
async def update_config(new_config: Dict[str, Any]):
    global config, ai_model, stt_manager
    save_config(new_config)
    config = new_config
    # Re-initialize managers that depend on config
    ai_model = AIModel(config)
    stt_manager = STTManager(config)
    return {"status": "success"}

@app.post("/stt/start")
async def start_stt():
    def sync_callback(text):
        # We need an event loop to run the async callback
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(stt_callback(text))
            else:
                loop.run_until_complete(stt_callback(text))
        except Exception as e:
            print(f"STT Callback Error: {e}")

    stt_manager.start_listening(sync_callback)
    return {"status": "listening"}

@app.post("/stt/stop")
async def stop_stt():
    stt_manager.stop_listening()
    return {"status": "stopped"}

# ========================================
# Player Persona Endpoints
# ========================================

@app.get("/players")
async def get_players():
    names = player_manager.get_player_names()
    results = []
    for name in names:
        player = player_manager.load_player(name)
        if player:
            results.append(player.to_dict())
    return results

@app.get("/players/{name}")
async def get_player(name: str):
    player = player_manager.load_player(name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player.to_dict()

@app.post("/players/create")
async def create_or_update_player(request: PlayerPersonaCreateRequest):
    from src.players.player_manager import Player
    
    existing = player_manager.load_player(request.name)
    if existing:
        # Update existing player
        existing.notes = request.backstory or existing.notes
        if request.stats:
            existing.reputation['_stats'] = request.stats
        player_manager.save_player(existing)
        return {"status": "updated", "message": f"Player {request.name} updated."}
    else:
        player = player_manager.create_player(
            name=request.name,
            race="Human",
            profession="Adventurer",
            notes=request.backstory or ""
        )
        if player and request.stats:
            player.reputation['_stats'] = request.stats
            player_manager.save_player(player)
        return {"status": "created", "message": f"Player {request.name} created."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
