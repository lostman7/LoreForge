"""
Speech-to-Text manager for voice input.
"""

import threading
import time
from typing import Callable, Optional

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

try:
    from openai import OpenAI
    WHISPER_API_AVAILABLE = True
except ImportError:
    WHISPER_API_AVAILABLE = False


import os
import contextlib
import sys

@contextlib.contextmanager
def ignore_stderr():
    """Context manager to suppress stderr output (handy for ALSA noise)."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(sys.stderr.fileno())
    os.dup2(devnull, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(old_stderr, sys.stderr.fileno())
        os.close(devnull)
        os.close(old_stderr)

class STTManager:
    """Manages speech-to-text functionality with multiple engine support."""

    def __init__(self, config: dict):
        self.config = config
        self.is_listening = False
        self.engine = config.get('stt', {}).get('engine', 'google')
        
        with ignore_stderr():
            self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
            try:
                self.microphone = sr.Microphone() if SPEECH_AVAILABLE else None
            except Exception as e:
                print(f"Microphone init failed: {e}")
                self.microphone = None
                
        self.callback: Optional[Callable[[str], None]] = None
        self.api_keys = config.get('apis', {})

    def start_listening(self, callback: Callable[[str], None]):
        """Start listening for speech input in a background thread."""
        if not SPEECH_AVAILABLE:
            print("Speech recognition not available. Install speechrecognition and pyaudio.")
            return

        self.callback = callback
        self.is_listening = True
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def stop_listening(self):
        """Stop the background listening thread."""
        self.is_listening = False

    def _listen_loop(self):
        """Internal loop for continuous recognition."""
        if not self.microphone or not self.recognizer:
            print("STT: Microphone or Recognizer not initialized.")
            return

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"STT Started (Engine: {self.engine})")
                
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=10)
                        text = self._recognize_audio(audio)
                        if text and self.callback:
                            self.callback(text)
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        if self.is_listening:
                            print(f"STT Background Error: {e}")
                        time.sleep(0.5)
        except Exception as e:
            print(f"STT: Failed to open microphone: {e}")
            self.is_listening = False

    def _recognize_audio(self, audio) -> Optional[str]:
        """Recognize audio using the selected engine."""
        if not self.recognizer:
            return None
            
        try:
            if self.engine == 'whisper' and WHISPER_API_AVAILABLE and self.api_keys.get('openai'):
                return self._recognize_whisper_api(audio)
            
            # Fallback to Google (Standard)
            return self.recognizer.recognize_google(
                audio, 
                language=self.config.get('stt', {}).get('language', 'en-US')
            )
        except Exception as e:
            print(f"Recognition failed: {e}")
            return None

    def _recognize_whisper_api(self, audio) -> str:
        """Use OpenAI Whisper API for high-quality transcription."""
        client = OpenAI(api_key=self.api_keys.get('openai'))
        
        # Save to temp wav for Whisper API
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            f.write(audio.get_wav_data())
            f.flush()
            
            with open(f.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                return transcript.text