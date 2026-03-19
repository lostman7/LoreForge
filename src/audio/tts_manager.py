"""
Text-to-Speech manager for handling voice output.
"""

import subprocess
import threading
from pathlib import Path
from typing import Optional

from src.presets.preset import VoiceConfig


class TTSManager:
    """Manages text-to-speech functionality."""

    def __init__(self, config: dict):
        self.config = config
        self.piper_path = self._find_piper_executable()

    def _find_piper_executable(self) -> Optional[str]:
        """Find Piper executable in system PATH or common locations."""
        # For now, assume piper is in PATH or we can download it
        # In production, this would check for piper executable
        return "piper"  # Placeholder

    def speak(self, text: str, voice_config: VoiceConfig):
        """Speak the given text using the specified voice configuration."""
        if voice_config.engine == "piper" and voice_config.model_path:
            self._speak_piper(text, voice_config)
        elif voice_config.engine == "elevenlabs" and voice_config.elevenlabs_voice_id:
            self._speak_elevenlabs(text, voice_config)
        else:
            # Fallback to system TTS
            self._speak_system(text)

    def _speak_piper(self, text: str, voice_config: VoiceConfig):
        """Speak using Piper TTS."""
        def run_tts():
            try:
                # Piper command: echo "text" | piper --model model.onnx --output_file -
                cmd = [
                    self.piper_path,
                    "--model", voice_config.model_path,
                    "--output_file", "-"
                ]

                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(input=text)

                if process.returncode == 0:
                    # Play the audio (this is simplified - in reality, pipe to aplay or similar)
                    pass
                else:
                    print(f"Piper TTS error: {stderr}")

            except Exception as e:
                print(f"TTS error: {e}")

        # Run in background thread
        threading.Thread(target=run_tts, daemon=True).start()

    def _speak_elevenlabs(self, text: str, voice_config: VoiceConfig):
        """Speak using ElevenLabs API."""
        try:
            import requests

            api_key = self.config.get('tts', {}).get('elevenlabs_api_key', '')
            if not api_key:
                print("ElevenLabs API key not configured")
                return

            voice_id = voice_config.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default voice

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }

            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                # Save and play audio
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    f.write(response.content)
                    temp_file = f.name

                # Play the audio file (platform-specific)
                self._play_audio_file(temp_file)
                os.unlink(temp_file)
            else:
                print(f"ElevenLabs API error: {response.status_code}")

        except ImportError:
            print("Requests library not available for ElevenLabs")
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")

    def _play_audio_file(self, file_path: str):
        """Play an audio file (cross-platform)."""
        import platform
        system = platform.system()

        try:
            if system == "Linux":
                subprocess.run(["aplay", file_path], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["afplay", file_path], check=True)
            elif system == "Windows":
                # Use PowerShell to play audio
                subprocess.run([
                    "powershell",
                    "-c",
                    f"(New-Object Media.SoundPlayer '{file_path}').PlaySync();"
                ], check=True)
            else:
                print(f"Audio playback not supported on {system}")
        except subprocess.CalledProcessError:
            print("Audio playback failed - install audio utilities")
        except Exception as e:
            print(f"Audio playback error: {e}")

    def _speak_system(self, text: str):
        """Fallback system TTS."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except ImportError:
            print(f"System TTS: {text}")