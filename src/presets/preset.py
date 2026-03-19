"""
Preset data classes for character configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class VoiceConfig:
    """Voice configuration for TTS."""
    engine: str = "piper"  # piper, elevenlabs, openai, system
    default_voice_engine: str = "local"  # local or cloud
    model_path: Optional[str] = None
    speaker_id: Optional[int] = None
    elevenlabs_voice_id: Optional[str] = None
    openai_voice: Optional[str] = None
    sample_file: Optional[str] = None  # For pre-recorded samples


@dataclass
class Preset:
    """Character preset configuration."""
    name: str
    profile_text: str
    avatar_path: Optional[str] = None
    background_path: Optional[str] = None
    voice_config: VoiceConfig = field(default_factory=VoiceConfig)
    config: Dict[str, Any] = field(default_factory=dict)
    folder_path: Optional[Path] = None

    # Character metadata
    character_name: str = ""
    job_title: str = ""
    location: str = ""
    short_lore: str = ""
    rag_memory_file: Optional[str] = None

    # Animation support
    background_frames: List[str] = field(default_factory=list)
    avatar_animation: bool = False

    # Music and Backstory
    music_path: Optional[str] = None
    backstory_audio_path: Optional[str] = None

    @classmethod
    def from_folder(cls, folder_path: Path) -> 'Preset':
        """Load preset from folder structure."""
        name = folder_path.name

        # Load profile
        profile_path = folder_path / 'profile.txt'
        profile_text = ""
        if profile_path.exists():
            try:
                profile_text = profile_path.read_text(encoding='utf-8')
            except Exception as e:
                print(f"Error reading profile.txt in {folder_path}: {e}")
                profile_text = profile_path.read_text(errors='replace')

        # Load assets
        avatar_path = folder_path / 'avatar.png'
        background_path = folder_path / 'background.png'

        # Load config
        config_path = folder_path / 'config.json'
        config = {}
        if config_path.exists():
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # Initialize voice config
        voice_config = VoiceConfig()
        default_voice_engine = config.get('default_voice_engine', 'local')

        # Handle voice directory structure
        voice_dir = folder_path / 'voice'
        if voice_dir.exists():
            local_dir = voice_dir / 'local'
            cloud_dir = voice_dir / 'cloud'

            if default_voice_engine == 'local' and local_dir.exists():
                # Load local voice models
                model_files = list(local_dir.glob('*.onnx')) + list(local_dir.glob('*.pth'))
                sample_files = list(local_dir.glob('*.wav'))
                if model_files:
                    voice_config.model_path = str(model_files[0])
                    voice_config.engine = "piper"
                if sample_files:
                    voice_config.sample_file = str(sample_files[0])

            elif default_voice_engine == 'cloud' and cloud_dir.exists():
                # Load cloud voice config
                cloud_config = cloud_dir / 'config.json'
                if cloud_config.exists():
                    with open(cloud_config, 'r') as f:
                        cloud_data = json.load(f)
                    voice_config.engine = cloud_data.get('engine', 'elevenlabs')
                    voice_config.elevenlabs_voice_id = cloud_data.get('elevenlabs_voice_id')
                    voice_config.openai_voice = cloud_data.get('openai_voice')

        # Override with main config if present
        if 'voice' in config:
            voice_data = config['voice']
            voice_config.engine = voice_data.get('engine', voice_config.engine)
            voice_config.default_voice_engine = voice_data.get('default_voice_engine', voice_config.default_voice_engine)
            if 'elevenlabs_voice_id' in voice_data:
                voice_config.elevenlabs_voice_id = voice_data['elevenlabs_voice_id']
            if 'openai_voice' in voice_data:
                voice_config.openai_voice = voice_data['openai_voice']

        # Load character metadata
        character_name = config.get('character_name', name)
        job_title = config.get('job_title', '')
        location = config.get('location', '')
        short_lore = config.get('short_lore', '')
        rag_memory_file = config.get('RAG_memory_file')

        # Handle animated backgrounds
        background_frames = []
        if background_path.exists():
            # Check if it's a GIF or if there are multiple frames
            if background_path.suffix.lower() == '.gif':
                background_frames = [str(background_path)]
            else:
                # Check for numbered frames (background_001.png, etc.)
                parent_dir = background_path.parent
                frame_pattern = f"{background_path.stem}_*.png"
                frames = list(parent_dir.glob(frame_pattern))
                if frames:
                    background_frames = sorted([str(f) for f in frames])
                else:
                    background_frames = [str(background_path)]

        avatar_animation = config.get('avatar_animation', False)

        # Detect character music file (<FolderName>.mp3)
        music_file = folder_path / f"{name}.mp3"
        music_path_str = str(music_file) if music_file.exists() else None

        # Detect backstory audio
        backstory_rel = config.get('asset_paths', {}).get('backstory_audio')
        backstory_path = folder_path / backstory_rel if backstory_rel else None
        backstory_path_str = str(backstory_path) if backstory_path and backstory_path.exists() else None

        return cls(
            name=name,
            profile_text=profile_text,
            avatar_path=str(avatar_path) if avatar_path.exists() else None,
            background_path=str(background_path) if background_path.exists() else None,
            voice_config=voice_config,
            config=config,
            character_name=character_name,
            job_title=job_title,
            location=location,
            short_lore=short_lore,
            rag_memory_file=rag_memory_file,
            background_frames=background_frames,
            avatar_animation=avatar_animation,
            folder_path=folder_path,
            music_path=music_path_str,
            backstory_audio_path=backstory_path_str
        )