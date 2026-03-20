"""
Text-to-Speech manager for handling voice output.
"""

import inspect
import os
import subprocess
import tempfile
import threading
from copy import deepcopy
from pathlib import Path
from typing import Optional

from src.presets.preset import VoiceConfig


class TTSManager:
    """Manages text-to-speech functionality."""

    def __init__(self, config: dict):
        self.config = config
        self.piper_path = self._find_piper_executable()
        self._qwen_model = None
        self._qwen_model_source = None
        self._qwen_model_lock = threading.Lock()
        self._qwen_prompt_cache: dict[tuple[str, str], object] = {}

    def _find_piper_executable(self) -> Optional[str]:
        """Find Piper executable in system PATH or common locations."""
        # For now, assume piper is in PATH or we can download it
        # In production, this would check for piper executable
        return "piper"  # Placeholder

    def speak(self, text: str, voice_config: VoiceConfig, preset=None):
        """Speak the given text using the specified voice configuration."""
        if voice_config.engine == "piper" and voice_config.model_path:
            self._speak_piper(text, voice_config)
        elif voice_config.engine == "elevenlabs" and voice_config.elevenlabs_voice_id:
            self._speak_elevenlabs(text, voice_config)
        elif voice_config.engine == "qwen3":
            self._speak_qwen3(text, voice_config, preset)
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

    def _speak_qwen3(self, text: str, voice_config: VoiceConfig, preset=None):
        """Speak using a local offline Qwen3-TTS model."""
        def run_tts():
            try:
                model = self._load_local_qwen_model(voice_config)
                wavs, sample_rate = self._generate_qwen_audio(model, text, voice_config, preset)
                if not wavs:
                    raise RuntimeError("Qwen3-TTS returned no audio frames")

                try:
                    import soundfile as sf
                except ImportError as exc:
                    raise RuntimeError("soundfile is required for offline Qwen3-TTS playback") from exc

                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                    temp_file = temp_audio.name

                try:
                    sf.write(temp_file, wavs[0], sample_rate)
                    self._play_audio_file(temp_file)
                finally:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
            except Exception as e:
                print(f"Offline Qwen3-TTS error: {e}")
                if self.config.get('tts', {}).get('fallback_to_system', True):
                    self._speak_system(text)

        threading.Thread(target=run_tts, daemon=True).start()

    def can_speak_with_qwen3(self, preset=None, voice_config: Optional[VoiceConfig] = None) -> tuple[bool, str]:
        """Validate that local Qwen3-TTS can run for the current character."""
        try:
            __import__('torch')
            __import__('soundfile')
            __import__('qwen_tts')
            qwen_voice = self.build_character_qwen_voice_config(preset, voice_config)
            self._resolve_local_qwen_model_path(qwen_voice)
            ref_audio, ref_text = self._resolve_qwen_reference_files(preset, qwen_voice)

            if ref_audio and ref_text:
                return True, ""

            if qwen_voice.qwen_voice:
                return True, ""

            if qwen_voice.qwen_instructions:
                return True, ""

            return False, (
                "This character is missing offline Qwen voice data. "
                "Add voice_reference.wav and voice_reference.txt to the character folder, "
                "or configure a built-in Qwen speaker/instructions."
            )
        except Exception as exc:
            return False, str(exc)

    def build_character_qwen_voice_config(self, preset=None, voice_config: Optional[VoiceConfig] = None) -> VoiceConfig:
        """Build the effective Qwen voice configuration for a character."""
        base_voice = deepcopy(voice_config or getattr(preset, 'voice_config', VoiceConfig()))
        tts_config = self.config.get('tts', {})

        model_size = tts_config.get('qwen3_model_size', '0.6B')
        default_model = 'Qwen3-TTS-12Hz-1.7B-Base' if model_size == '1.6B' else 'Qwen3-TTS-12Hz-0.6B-Base'

        base_voice.engine = "qwen3"
        base_voice.qwen_model = base_voice.qwen_model or tts_config.get('qwen3_model') or default_model
        base_voice.qwen_model_path = base_voice.qwen_model_path or tts_config.get('qwen3_model_path')
        base_voice.qwen_tokenizer_path = base_voice.qwen_tokenizer_path or tts_config.get('qwen3_tokenizer_path')
        base_voice.qwen_language = base_voice.qwen_language or tts_config.get('qwen3_language') or 'Auto'
        base_voice.qwen_instructions = base_voice.qwen_instructions or tts_config.get('qwen3_instructions')
        return base_voice

    def _load_local_qwen_model(self, voice_config: VoiceConfig):
        """Load a local Qwen3-TTS model on demand."""
        try:
            import torch
            from qwen_tts import Qwen3TTSModel
        except ImportError as exc:
            raise RuntimeError(
                "Offline Qwen3-TTS requires the qwen-tts and torch packages to be installed."
            ) from exc

        model_source = self._resolve_local_qwen_model_path(voice_config)
        tokenizer_source = self._resolve_local_qwen_tokenizer_path(voice_config)

        if self._qwen_model is not None and self._qwen_model_source == model_source:
            return self._qwen_model

        with self._qwen_model_lock:
            if self._qwen_model is not None and self._qwen_model_source == model_source:
                return self._qwen_model

            # Offload old model if present
            if self._qwen_model is not None:
                print(f"[TTS] Offloading old model: {self._qwen_model_source}")
                self._qwen_model.to("cpu")
                del self._qwen_model
                self._qwen_model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            device_map = self._get_qwen_device_map(torch)
            dtype = self._get_qwen_dtype(torch, device_map)
            model_kwargs = {"device_map": device_map}

            if dtype is not None:
                model_kwargs["dtype"] = dtype

            attn_implementation = self.config.get('tts', {}).get('qwen3_attention')
            if attn_implementation and device_map != "cpu":
                model_kwargs["attn_implementation"] = attn_implementation

            if tokenizer_source:
                param_names = inspect.signature(Qwen3TTSModel.from_pretrained).parameters
                if "tokenizer_name_or_path" in param_names:
                    model_kwargs["tokenizer_name_or_path"] = tokenizer_source
                elif "tokenizer_path" in param_names:
                    model_kwargs["tokenizer_path"] = tokenizer_source

            self._qwen_model = Qwen3TTSModel.from_pretrained(model_source, **model_kwargs)
            self._qwen_model_source = model_source
            self._qwen_prompt_cache.clear()
            return self._qwen_model

    def _generate_qwen_audio(self, model, text: str, voice_config: VoiceConfig, preset=None):
        """Generate audio from the local Qwen3-TTS model."""
        qwen_voice = self.build_character_qwen_voice_config(preset, voice_config)
        language = qwen_voice.qwen_language or "Auto"
        instructions = qwen_voice.qwen_instructions or ""
        ref_audio, ref_text = self._resolve_qwen_reference_files(preset, qwen_voice)

        if ref_audio and ref_text and hasattr(model, "generate_voice_clone"):
            prompt_key = (str(ref_audio), ref_text)
            voice_clone_prompt = self._qwen_prompt_cache.get(prompt_key)
            if voice_clone_prompt is None and hasattr(model, "create_voice_clone_prompt"):
                voice_clone_prompt = model.create_voice_clone_prompt(
                    ref_audio=str(ref_audio),
                    ref_text=ref_text,
                    x_vector_only_mode=self.config.get('tts', {}).get('qwen3_x_vector_only_mode', False),
                )
                self._qwen_prompt_cache[prompt_key] = voice_clone_prompt

            if voice_clone_prompt is not None:
                return model.generate_voice_clone(
                    text=text,
                    language=language,
                    voice_clone_prompt=voice_clone_prompt,
                )

            return model.generate_voice_clone(
                text=text,
                language=language,
                ref_audio=str(ref_audio),
                ref_text=ref_text,
            )

        if qwen_voice.qwen_voice and hasattr(model, "generate_custom_voice"):
            return model.generate_custom_voice(
                text=text,
                language=language,
                speaker=qwen_voice.qwen_voice,
                instruct=instructions or "",
            )

        if instructions and hasattr(model, "generate_voice_design"):
            return model.generate_voice_design(
                text=text,
                language=language,
                instruct=instructions,
            )

        raise RuntimeError(
            "Offline Qwen3-TTS needs either character reference files "
            "(voice_reference.wav + voice_reference.txt), a built-in Qwen speaker, or voice-design instructions."
        )

    def _resolve_local_qwen_model_path(self, voice_config: VoiceConfig) -> str:
        """Resolve the local Qwen model directory."""
        tts_config = self.config.get('tts', {})
        models_dir = Path(tts_config.get('qwen3_models_dir', './models'))

        model_size = tts_config.get('qwen3_model_size', '0.6B')
        default_model = 'Qwen3-TTS-12Hz-1.7B-Base' if model_size == '1.6B' else 'Qwen3-TTS-12Hz-0.6B-Base'

        # Priority: 1. Voice specific path, 2. Config specific path, 3. Size-based default
        # We ignore qwen3_model if it's one of the defaults to allow the size setting to drive it.

        model_hint = voice_config.qwen_model_path or tts_config.get('qwen3_model_path')

        if not model_hint:
            custom_model = voice_config.qwen_model or tts_config.get('qwen3_model')
            if custom_model and custom_model not in ['Qwen3-TTS-12Hz-0.6B-Base', 'Qwen3-TTS-12Hz-1.7B-Base']:
                model_hint = custom_model
            else:
                model_hint = default_model

        resolved = self._resolve_local_path_hint(model_hint, models_dir)
        if resolved:
            return str(resolved)

        raise FileNotFoundError(
            f"Offline Qwen3-TTS model not found. Download '{model_hint}' into {models_dir.resolve()} "
            "or set tts.qwen3_model_path in config.json."
        )

    def _resolve_local_qwen_tokenizer_path(self, voice_config: VoiceConfig) -> Optional[str]:
        """Resolve the optional local tokenizer directory."""
        tts_config = self.config.get('tts', {})
        models_dir = Path(tts_config.get('qwen3_models_dir', './models'))
        tokenizer_hint = voice_config.qwen_tokenizer_path or tts_config.get('qwen3_tokenizer_path')
        if not tokenizer_hint:
            default_candidate = models_dir / 'Qwen3-TTS-Tokenizer-12Hz'
            return str(default_candidate) if default_candidate.exists() else None

        resolved = self._resolve_local_path_hint(tokenizer_hint, models_dir)
        return str(resolved) if resolved else None

    def _resolve_local_path_hint(self, path_hint: str, base_dir: Path) -> Optional[Path]:
        """Resolve a local directory hint into an existing path."""
        hint_path = Path(path_hint)
        candidate_paths = []
        if hint_path.is_absolute():
            candidate_paths.append(hint_path)
        else:
            candidate_paths.extend([
                Path.cwd() / hint_path,
                base_dir / hint_path,
                base_dir / hint_path.name,
            ])
        for candidate in candidate_paths:
            if candidate.exists():
                return candidate.resolve()
        return None

    def _resolve_qwen_reference_files(self, preset, voice_config: VoiceConfig) -> tuple[Optional[Path], Optional[str]]:
        """Find the current character's voice clone reference files."""
        audio_candidates = []
        if voice_config.qwen_reference_audio:
            audio_candidates.append(Path(voice_config.qwen_reference_audio))
        if preset and getattr(preset, 'folder_path', None):
            folder = Path(preset.folder_path)
            audio_candidates.extend([
                folder / 'voice_reference.wav',
                folder / 'voice' / 'voice_reference.wav',
                folder / 'voice' / 'local' / 'voice_reference.wav',
            ])

        text_candidates = []
        if voice_config.qwen_reference_text:
            text_candidates.append(Path(voice_config.qwen_reference_text))
        if preset and getattr(preset, 'folder_path', None):
            folder = Path(preset.folder_path)
            text_candidates.extend([
                folder / 'voice_reference.txt',
                folder / 'voice' / 'voice_reference.txt',
                folder / 'voice' / 'local' / 'voice_reference.txt',
            ])

        reference_audio = next((candidate for candidate in audio_candidates if candidate.exists()), None)
        reference_text_path = next((candidate for candidate in text_candidates if candidate.exists()), None)

        if not reference_audio or not reference_text_path:
            return None, None

        return reference_audio, reference_text_path.read_text(encoding='utf-8').strip()

    def _get_qwen_device_map(self, torch_module) -> str:
        """Pick the device map for local Qwen inference."""
        configured_device = self.config.get('tts', {}).get('qwen3_device', 'auto')
        if configured_device and configured_device != 'auto':
            return configured_device
        return "cuda:0" if torch_module.cuda.is_available() else "cpu"

    def _get_qwen_dtype(self, torch_module, device_map: str):
        """Select an inference dtype for local Qwen inference."""
        configured_dtype = self.config.get('tts', {}).get('qwen3_dtype', 'auto')
        if configured_dtype == 'float32':
            return torch_module.float32
        if configured_dtype == 'float16':
            return torch_module.float16
        if configured_dtype == 'bfloat16':
            return torch_module.bfloat16
        return torch_module.float16 if device_map != "cpu" else torch_module.float32

    def _play_audio_file(self, file_path: str):
        """Play an audio file (cross-platform)."""
        import platform
        system = platform.system()

        try:
            if system == "Linux":
                for player in (["aplay", file_path], ["ffplay", "-nodisp", "-autoexit", file_path]):
                    try:
                        subprocess.run(player, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue
                try:
                    from playsound import playsound
                    playsound(file_path)
                    return
                except Exception:
                    raise RuntimeError("No Linux audio playback utility available")
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
        except FileNotFoundError:
            print("Audio playback utility not found on this system")
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
