"""
AI model interface for generating responses.
"""

from typing import Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from src.presets.preset import Preset


class AIModel:
    """Interface for multiple AI model backends."""

    def __init__(self, config: dict):
        self.config = config
        self.api_keys = config.get('apis', {})
        self.ai_config = config.get('ai', {})
        self.backend = self.ai_config.get('backend', 'ollama')
        self.model = self.ai_config.get('model', 'llama3.2:3b')
        self.temperature = self.ai_config.get('temperature', 0.8)
        self.max_tokens = self.ai_config.get('max_tokens', 1024)
        self.num_ctx = self.ai_config.get('num_ctx', 4096)

    def generate_response(self, message: str, context: str, preset: Preset, extra_context: dict = None) -> str:
        """Generate response using current backend."""
        # Merge preset-specific settings if available
        preset_config = preset.config.get('chat_behavior', {})
        temp = preset_config.get('temperature', self.temperature)
        tokens = preset_config.get('max_response_length', self.max_tokens)

        # Build prompt with roleplay context
        system_prompt = self._build_system_prompt(preset, context, extra_context or {})

        try:
            if self.backend == 'ollama' and OLLAMA_AVAILABLE:
                return self._generate_ollama(system_prompt, message, temp, tokens)
            
            elif self.backend == 'openai' and OPENAI_AVAILABLE:
                return self._generate_openai(system_prompt, message, temp, tokens)
            
            elif self.backend == 'claude' and ANTHROPIC_AVAILABLE:
                return self._generate_claude(system_prompt, message, temp, tokens)
            
            elif self.backend == 'grok' and OPENAI_AVAILABLE:
                return self._generate_grok(system_prompt, message, temp, tokens)
            
            elif self.backend == 'lmstudio' and OPENAI_AVAILABLE:
                return self._generate_lmstudio(system_prompt, message, temp, tokens)

            elif self.backend == 'llama_cloud' and OPENAI_AVAILABLE:
                return self._generate_llama_cloud(system_prompt, message, temp, tokens)

            return self._generate_fallback(message, preset)
        except Exception as e:
            return f"Backend Error ({self.backend}): {str(e)}"

    def _build_system_prompt(self, preset: Preset, context: str, extra_context: dict = None) -> str:
        # Get affinity from player data
        affinity_val = 0
        if extra_context and 'persona' in extra_context:
            stats = extra_context['persona'].get('stats', {})
            # This logic assumes affinity is stored in a way we can extract or pass
            affinity_val = extra_context.get('current_affinity', 0)

        prompt = f"""You are roleplaying as {preset.character_name}.
Role: {preset.job_title}
Location: {preset.location}
Affinity with Player: {affinity_val}/100
Backstory: {preset.profile_text}

Immersive Memory:
{context}"""

        # Add weather mood context
        if extra_context and extra_context.get('weather_prompt'):
            prompt += f"\n\nCurrent Weather & Mood:\n{extra_context['weather_prompt']}"

        # Add player persona context
        if extra_context and extra_context.get('persona'):
            persona = extra_context['persona']
            prompt += f"\n\nThe person you are speaking with is {persona.get('name', 'an adventurer')}."
            if persona.get('backstory'):
                prompt += f" Their backstory: {persona['backstory']}"
            if persona.get('gold') is not None:
                prompt += f" They currently have {persona['gold']} gold coins."
            if persona.get('stats'):
                stats = persona['stats']
                stats_str = ', '.join([f"{k}: {v}" for k, v in stats.items() if v])
                if stats_str:
                    prompt += f" Their stats: {stats_str}."

        if extra_context and extra_context.get('economy'):
            economy = extra_context['economy']
            prompt += (
                f"\n\nEconomy & Trading State:\n"
                f"- Your current gold: {economy.get('npc_gold', 0)}\n"
                f"- Your pricing style: {economy.get('pricing_style', 'standard')}\n"
                f"- Your available shop stock: {economy.get('shop_stock', 'no stock listed')}\n"
                "- Keep trade offers grounded in the listed stock and prices when acting as a merchant."
            )

        prompt += "\n\nRespond in-character (first person). Be expressive and true to your lore."
        return prompt

    def _generate_ollama(self, system: str, message: str, temp: float, tokens: int) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': message}
            ],
            options={
                'temperature': temp, 
                'num_predict': tokens,
                'num_ctx': self.num_ctx
            }
        )
        # Handle both dict and pydantic object responses
        if hasattr(response, 'message'):
            return response.message.content
        return response['message']['content']

    def _generate_openai(self, system: str, message: str, temp: float, tokens: int) -> str:
        client = OpenAI(api_key=self.api_keys.get('openai'))
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            temperature=temp,
            max_tokens=tokens
        )
        return response.choices[0].message.content

    def _generate_claude(self, system: str, message: str, temp: float, tokens: int) -> str:
        client = anthropic.Anthropic(api_key=self.api_keys.get('claude'))
        response = client.messages.create(
            model=self.model or "claude-3-5-sonnet-20240620",
            max_tokens=tokens,
            temperature=temp,
            system=system,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

    def _generate_grok(self, system: str, message: str, temp: float, tokens: int) -> str:
        # Grok uses OpenAI-compatible API
        client = OpenAI(api_key=self.api_keys.get('grok'), base_url="https://api.x.ai/v1")
        response = client.chat.completions.create(
            model=self.model or "grok-beta",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            temperature=temp,
            max_tokens=tokens
        )
        return response.choices[0].message.content

    def _generate_lmstudio(self, system: str, message: str, temp: float, tokens: int) -> str:
        # LM Studio uses OpenAI-compatible API
        base_url = self.api_keys.get('lmstudio') or "http://localhost:1234/v1"
        client = OpenAI(api_key="not-needed", base_url=base_url)
        response = client.chat.completions.create(
            model=self.model or "local-model",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            temperature=temp,
            max_tokens=tokens
        )
        return response.choices[0].message.content

    def _generate_llama_cloud(self, system: str, message: str, temp: float, tokens: int) -> str:
        # Llama Cloud uses OpenAI-compatible API
        client = OpenAI(api_key=self.api_keys.get('llama_cloud'), base_url="https://api.llama-api.com")
        response = client.chat.completions.create(
            model=self.model or "llama3.1-70b",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            temperature=temp,
            max_tokens=tokens
        )
        return response.choices[0].message.content

    def _generate_fallback(self, message: str, preset: Preset) -> str:
        return f"[System: {self.backend} backend or keys missing] As {preset.character_name}, I received: {message}"
