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
        self.recognizer = None
        self.microphone = None
        self.listen_thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable[[str], None]] = None
        self.api_keys = config.get('apis', {})
        self.stt_config = config.get('stt', {})
        self._initialize_audio_input()

    def _initialize_audio_input(self):
        """Initialize recognizer and microphone lazily and safely."""
        if not SPEECH_AVAILABLE:
            return

        with ignore_stderr():
            if self.recognizer is None:
                self.recognizer = sr.Recognizer()
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = self.stt_config.get('pause_threshold', 0.8)
                self.recognizer.non_speaking_duration = self.stt_config.get('non_speaking_duration', 0.5)
            if self.microphone is None:
                try:
                    self.microphone = sr.Microphone()
                except Exception as e:
                    print(f"Microphone init failed: {e}")
                    self.microphone = None

    def start_listening(self, callback: Callable[[str], None]) -> bool:
        """Start listening for speech input in a background thread."""
        if not SPEECH_AVAILABLE:
            print("Speech recognition not available. Install speechrecognition and pyaudio.")
            return False
        if self.is_listening:
            return True
        self._initialize_audio_input()
        if not self.microphone or not self.recognizer:
            print("STT unavailable: microphone or recognizer could not be initialized.")
            return False

        self.callback = callback
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        return True

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
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self.stt_config.get('ambient_noise_duration', 0.8)
                )
                print(f"STT Started (Engine: {self.engine})")
                
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=self.stt_config.get('timeout', 5),
                            phrase_time_limit=self.stt_config.get('phrase_limit', 10)
                        )
                        text = self._recognize_audio(audio)
                        if text and self.callback:
                            self.callback(text)
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        if self.is_listening:
                            print(f"STT request error: {e}")
                        time.sleep(1.0)
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
            if self.engine in {'whisper', 'openai'} and WHISPER_API_AVAILABLE and self.api_keys.get('openai'):
                return self._recognize_whisper_api(audio)
            
            # Fallback to Google (Standard)
            return self.recognizer.recognize_google(
                audio, 
                language=self.config.get('stt', {}).get('language', 'en-US')
            )
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Recognition request failed: {e}")
            return None
        except Exception as e:
            print(f"Recognition failed: {e}")
            return None

    def _recognize_whisper_api(self, audio) -> str:
        """Use OpenAI Whisper API for high-quality transcription."""
        client = OpenAI(api_key=self.api_keys.get('openai'))
        model_name = self.stt_config.get('openai_model', 'whisper-1')
        
        # Save to temp wav for Whisper API
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            f.write(audio.get_wav_data())
            f.flush()
            
            with open(f.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=model_name,
                    file=audio_file,
                    language=self.stt_config.get('language', 'en-US').split('-')[0]
                )
                return transcript.text
