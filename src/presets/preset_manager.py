"""
Manager for loading and managing character presets.
"""

import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any

from .preset import Preset


class PresetManager:
    """Manages character presets."""

    def __init__(self, presets_dir: Optional[str] = None):
        self.presets_dir = Path(presets_dir) if presets_dir else Path(__file__).parent.parent.parent / 'knowledge'
        self.presets_dir.mkdir(exist_ok=True)
        self._presets_cache: dict[str, Preset] = {}

    def get_preset_names(self) -> List[str]:
        """Get list of available preset names."""
        print(f"DEBUG: Scanning for presets in {self.presets_dir.absolute()}")
        if not self.presets_dir.exists():
            print(f"DEBUG: Presets directory {self.presets_dir.absolute()} does not exist.")
            return []

        names = [d.name for d in self.presets_dir.iterdir() if d.is_dir()]
        print(f"DEBUG: Found preset folders: {names}")
        return names

    def load_preset(self, name: str) -> Optional[Preset]:
        """Load a preset by name."""
        if name in self._presets_cache:
            return self._presets_cache[name]

        preset_path = self.presets_dir / name
        print(f"DEBUG: Attempting to load preset from {preset_path.absolute()}")
        if not preset_path.exists() or not preset_path.is_dir():
            print(f"DEBUG: Preset path {preset_path.absolute()} does not exist or is not a directory.")
            return None

        try:
            preset = Preset.from_folder(preset_path)
            self._presets_cache[name] = preset
            print(f"DEBUG: Successfully loaded preset {name}")
            return preset
        except Exception as e:
            import traceback
            print(f"Error loading preset {name}: {e}")
            traceback.print_exc()
            return None

    def refresh_presets(self):
        """Clear the cache and re-scan presets."""
        self._presets_cache.clear()
        return self.get_all_presets()

    def reload_preset(self, name: str) -> Optional[Preset]:
        """Reload a preset from disk."""
        if name in self._presets_cache:
            del self._presets_cache[name]
        return self.load_preset(name)

    def get_all_presets(self) -> List[Preset]:
        """Get all loaded presets."""
        names = self.get_preset_names()
        print(f"DEBUG: Identified preset names from disk: {names}")
        presets = []
        for name in names:
            preset = self.load_preset(name)
            if preset:
                presets.append(preset)
            else:
                print(f"DEBUG: Failed to load preset object for {name}")
        return presets

    def rename_preset(self, old_name: str, new_name: str):
        """Rename a preset folder and update all references."""
        old_path = self.presets_dir / old_name
        new_path = self.presets_dir / new_name

        if not old_path.exists():
            raise FileNotFoundError(f"Preset '{old_name}' not found")

        if new_path.exists():
            raise FileExistsError(f"Preset '{new_name}' already exists")

        # Rename the folder
        old_path.rename(new_path)

        # Update config.json with new name
        config_path = new_path / 'config.json'
        if config_path.exists():
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)

            config['character_name'] = new_name

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

        # Clear cache
        if old_name in self._presets_cache:
            del self._presets_cache[old_name]

    def delete_preset(self, name: str):
        """Delete a preset and all associated files."""
        preset_path = self.presets_dir / name

        if not preset_path.exists():
            raise FileNotFoundError(f"Preset '{name}' not found")

        # Remove the entire folder
        import shutil
        shutil.rmtree(preset_path)

        # Clear cache
        if name in self._presets_cache:
            del self._presets_cache[name]

        # Note: Memory files and other assets are left intact for safety
        # They can be cleaned up manually if needed

    def create_character(self, character_data: Dict[str, Any]) -> bool:
        """Create a new character preset with full asset management."""
        try:
            folder_name = character_data['folder_name']
            preset_dir = self.presets_dir / folder_name
            preset_dir.mkdir(exist_ok=True)

            # Create subdirectories
            voice_dir = preset_dir / 'voice'
            voice_dir.mkdir(exist_ok=True)

            if character_data['voice_engine'] == 'local':
                local_voice_dir = voice_dir / 'local'
                local_voice_dir.mkdir(exist_ok=True)
            else:
                cloud_voice_dir = voice_dir / 'cloud'
                cloud_voice_dir.mkdir(exist_ok=True)

            # Copy avatar if provided
            if character_data.get('avatar_path'):
                avatar_dest = preset_dir / 'avatar.png'
                shutil.copy2(character_data['avatar_path'], avatar_dest)

            # Copy background if provided
            if character_data.get('background_path'):
                background_dest = preset_dir / 'background.png'
                shutil.copy2(character_data['background_path'], background_dest)

            # Handle voice files
            if character_data['voice_engine'] == 'local' and character_data.get('voice_file_path'):
                voice_dest = voice_dir / 'local' / Path(character_data['voice_file_path']).name
                shutil.copy2(character_data['voice_file_path'], voice_dest)

            # Create profile.txt
            profile_path = preset_dir / 'profile.txt'
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(character_data['profile_text'])

            # Create config.json with full metadata
            config = {
                'character_name': character_data['character_name'],
                'job_title': character_data['job_title'],
                'location': character_data['location'],
                'short_lore': character_data['short_lore'],
                'default_voice_engine': character_data['voice_engine'],
                'RAG_memory_file': f"memory_{folder_name}.db",
                'avatar_animation': character_data.get('avatar_animation', False),
                'chat_behavior': {
                    'temperature': character_data['temperature'],
                    'max_response_length': character_data['max_length'],
                    'personality_weight': character_data['personality_weight']
                },
                'voice': {
                    'engine': 'piper' if character_data['voice_engine'] == 'local' else character_data.get('cloud_provider', 'elevenlabs'),
                    'default_voice_engine': character_data['voice_engine']
                },
                'appearance': {
                    'theme': 'fantasy',
                    'accent_color': '#4a90e2'
                },
                'memory': {
                    'importance_keywords': character_data['memory_keywords'].split(',') if character_data.get('memory_keywords') else [],
                    'context_window': 10
                }
            }

            # Add cloud voice configuration
            if character_data['voice_engine'] == 'cloud':
                if character_data.get('cloud_provider') == 'elevenlabs':
                    config['voice']['elevenlabs_voice_id'] = character_data.get('voice_id', '')
                elif character_data.get('cloud_provider') == 'openai':
                    config['voice']['openai_voice'] = character_data.get('voice_id', 'alloy')

                # Create cloud config file
                cloud_config = {
                    'engine': character_data.get('cloud_provider', 'elevenlabs'),
                    'elevenlabs_voice_id': character_data.get('voice_id', '') if character_data.get('cloud_provider') == 'elevenlabs' else '',
                    'openai_voice': character_data.get('voice_id', 'alloy') if character_data.get('cloud_provider') == 'openai' else ''
                }

                cloud_config_path = voice_dir / 'cloud' / 'config.json'
                with open(cloud_config_path, 'w') as f:
                    json.dump(cloud_config, f, indent=2)

            # Save main config
            config_path = preset_dir / 'config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            # Clear cache to force reload
            if folder_name in self._presets_cache:
                del self._presets_cache[folder_name]

            return True

        except Exception as e:
            print(f"Error creating character: {e}")
            return False

    def clone_preset(self, source_name: str, target_name: str) -> bool:
        """Clone an existing preset to create a new character."""
        try:
            source_dir = self.presets_dir / source_name
            target_dir = self.presets_dir / target_name

            if not source_dir.exists():
                return False

            # Copy entire directory
            shutil.copytree(source_dir, target_dir)

            # Update config with new name
            config_path = target_dir / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)

                config['character_name'] = target_name.replace('_', ' ').title()
                config['RAG_memory_file'] = f"memory_{target_name}.db"

                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)

            # Update profile if it references the old name
            profile_path = target_dir / 'profile.txt'
            if profile_path.exists():
                try:
                    profile_text = profile_path.read_text(encoding='utf-8')
                except Exception as e:
                    print(f"Error reading profile.txt in {profile_path}: {e}")
                    profile_text = profile_path.read_text(errors='replace')
                
                # Simple replacement - could be more sophisticated
                new_profile = profile_text.replace(source_name, target_name)
                profile_path.write_text(new_profile, encoding='utf-8')

            return True

        except Exception as e:
            print(f"Error cloning preset: {e}")
            return False

    def create_simple_preset(self, character_data: Dict[str, Any]) -> bool:
        """Create a character preset using simplified auto-linking logic."""
        try:
            name = character_data['name']
            preset_dir = self.presets_dir / name
            preset_dir.mkdir(exist_ok=True)

            # Create Documents folder for character memory/RAG
            doc_dir = preset_dir / 'Documents'
            doc_dir.mkdir(exist_ok=True)

            # Create rag/ folder for RAG data
            rag_dir = preset_dir / 'rag'
            rag_dir.mkdir(exist_ok=True)

            # Create images/ folder for character visuals
            images_dir = preset_dir / 'images'
            images_dir.mkdir(exist_ok=True)

            # Handle base64 avatar image
            if character_data.get('avatar_base64'):
                import base64
                avatar_data = base64.b64decode(character_data['avatar_base64'])
                # Save to images/ subfolder
                avatar_images_path = images_dir / 'avatar.png'
                with open(avatar_images_path, 'wb') as f:
                    f.write(avatar_data)
                # Also save to root for backward compatibility (tile loading)
                avatar_root_path = preset_dir / 'avatar.png'
                with open(avatar_root_path, 'wb') as f:
                    f.write(avatar_data)
            else:
                # Handle legacy detected_assets
                detected_assets = character_data.get('detected_assets', {})
                avatar_src = detected_assets.get('avatar')
                if avatar_src:
                    shutil.copy2(avatar_src, preset_dir / 'avatar.png')
                    shutil.copy2(avatar_src, images_dir / 'avatar.png')

            # Handle base64 background image
            if character_data.get('background_base64'):
                import base64
                bg_data = base64.b64decode(character_data['background_base64'])
                # Save to images/ subfolder
                bg_images_path = images_dir / 'background.png'
                with open(bg_images_path, 'wb') as f:
                    f.write(bg_data)
                # Also save to root for backward compatibility
                bg_root_path = preset_dir / 'background.png'
                with open(bg_root_path, 'wb') as f:
                    f.write(bg_data)
            else:
                # Handle legacy detected_assets
                detected_assets = character_data.get('detected_assets', {})
                background_src = detected_assets.get('background')
                if background_src:
                    shutil.copy2(background_src, preset_dir / 'background.png')
                    shutil.copy2(background_src, images_dir / 'background.png')

            # Handle base64 music file
            if character_data.get('music_base64'):
                import base64
                music_data = base64.b64decode(character_data['music_base64'])
                music_path = preset_dir / f"{name}.mp3"
                with open(music_path, 'wb') as f:
                    f.write(music_data)

            # Handle base64 RAG data
            if character_data.get('rag_base64'):
                import base64
                rag_data = base64.b64decode(character_data['rag_base64'])
                rag_path = rag_dir / "character_data.txt" # Default name
                # Try to guess extension or use generic .txt
                with open(rag_path, 'wb') as f:
                    f.write(rag_data)

            # Handle base64 backstory audio
            if character_data.get('backstory_audio_base64'):
                import base64
                # Create Background folder
                background_folder = preset_dir / 'Background'
                background_folder.mkdir(exist_ok=True)
                
                audio_data = base64.b64decode(character_data['backstory_audio_base64'])
                audio_path = background_folder / "backstory.mp3"
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                backstory_audio_rel_path = "Background/backstory.mp3"
            else:
                backstory_audio_rel_path = None

            # Create profile.txt in character folder

            # Create profile.txt in character folder
            profile_text = f"This is a roleplay session for LoreForge.\n\n"
            profile_text += character_data.get('description', f'You are {name}.')
            if character_data.get('role'):
                profile_text += f' You are a {character_data["role"]}.'
            if character_data.get('location'):
                profile_text += f' You are located in {character_data["location"]}.'

            profile_path = preset_dir / 'profile.txt'
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(profile_text)

            # Create config.json in character folder
            config = {
                'character_name': name,
                'job_title': character_data.get('role', ''),
                'location': character_data.get('location', ''),
                'short_lore': character_data.get('description', ''),
                'summary': character_data.get('description', ''),
                'default_voice_engine': character_data.get('voice_mode', 'local'),
                'RAG_memory_file': f"{name}_memory.json",
                'avatar_animation': False,
                'chat_behavior': {
                    'temperature': 0.8,
                    'max_response_length': 150,
                    'personality_weight': 0.8
                },
                'voice': {
                    'engine': 'piper',
                    'default_voice_engine': 'local'
                },
                'appearance': {
                    'theme': 'fantasy',
                    'accent_color': '#4a90e2'
                },
                'memory': {
                    'importance_keywords': [name.lower(), character_data.get('role', '').lower()],
                    'context_window': 10
                },
                'asset_paths': {
                    'avatar': 'images/avatar.png',
                    'background': 'images/background.png',
                    'documents': 'Documents',
                    'rag': 'rag',
                    'backstory_audio': backstory_audio_rel_path
                }
            }

            config_path = preset_dir / 'config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            # Clear cache to force reload
            if name in self._presets_cache:
                del self._presets_cache[name]

            return True

        except Exception as e:
            print(f"Error creating simple preset: {e}")
            return False

    def validate_preset(self, preset_name: str) -> dict:
        """Validate a preset and return validation results."""
        preset_dir = self.presets_dir / preset_name
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_files': [],
            'recommendations': []
        }

        if not preset_dir.exists():
            validation_results['valid'] = False
            validation_results['errors'].append(f"Preset directory does not exist: {preset_dir}")
            return validation_results

        # Check required files
        required_files = ['profile.txt', 'config.json']
        for file in required_files:
            if not (preset_dir / file).exists():
                validation_results['valid'] = False
                validation_results['errors'].append(f"Missing required file: {file}")
                validation_results['missing_files'].append(file)

        # Check config.json structure
        config_path = preset_dir / 'config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Check for required config fields
                if 'character_name' not in config:
                    validation_results['warnings'].append("Missing character_name in config.json")
                if 'default_voice_engine' not in config:
                    validation_results['warnings'].append("Missing default_voice_engine in config.json")

                # Check voice configuration
                if config.get('default_voice_engine') == 'local':
                    voice_dir = preset_dir / 'voice' / 'local'
                    if not voice_dir.exists():
                        validation_results['warnings'].append("Local voice directory missing")
                    else:
                        voice_files = list(voice_dir.glob('*.onnx')) + list(voice_dir.glob('*.pth'))
                        if not voice_files:
                            validation_results['warnings'].append("No voice model files found in local voice directory")

                elif config.get('default_voice_engine') == 'cloud':
                    cloud_config = preset_dir / 'voice' / 'cloud' / 'config.json'
                    if not cloud_config.exists():
                        validation_results['warnings'].append("Cloud voice configuration missing")

            except json.JSONDecodeError:
                validation_results['valid'] = False
                validation_results['errors'].append("Invalid JSON in config.json")

        # Check optional assets
        optional_files = ['avatar.png', 'background.png']
        for file in optional_files:
            if not (preset_dir / file).exists():
                validation_results['recommendations'].append(f"Consider adding {file} for better visual experience")

        # Check voice directory structure
        voice_dir = preset_dir / 'voice'
        if voice_dir.exists():
            if not (voice_dir / 'local').exists() and not (voice_dir / 'cloud').exists():
                validation_results['warnings'].append("No voice subdirectories (local/cloud) found")

        return validation_results

    def get_preset_validation_report(self, preset_name: str) -> str:
        """Get a human-readable validation report for a preset."""
        results = self.validate_preset(preset_name)

        report = f"Preset Validation Report: {preset_name}\n"
        report += "=" * 40 + "\n"

        if results['valid']:
            report += "✅ Status: VALID\n"
        else:
            report += "❌ Status: INVALID\n"

        if results['errors']:
            report += "\nErrors:\n"
            for error in results['errors']:
                report += f"  - {error}\n"

        if results['warnings']:
            report += "\nWarnings:\n"
            for warning in results['warnings']:
                report += f"  - {warning}\n"

        if results['recommendations']:
            report += "\nRecommendations:\n"
            for rec in results['recommendations']:
                report += f"  - {rec}\n"

        return report