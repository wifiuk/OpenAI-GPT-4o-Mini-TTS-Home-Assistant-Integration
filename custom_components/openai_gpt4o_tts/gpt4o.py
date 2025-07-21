import logging
import requests

from .const import (
    CONF_VOICE,
    CONF_INSTRUCTIONS,
    CONF_SPEED,
    DEFAULT_SPEED,
)

_LOGGER = logging.getLogger(__name__)


class GPT4oClient:
    """Handles direct calls to OpenAI's /v1/audio/speech for GPT-4o TTS."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        # Always set your API key
        self._api_key = entry.data["api_key"]

        # Pull default voice/instructions from options first, then legacy data
        opts = getattr(entry, "options", {}) or {}
        self._voice = opts.get(CONF_VOICE, entry.data.get(CONF_VOICE))
        self._instructions = opts.get(CONF_INSTRUCTIONS, entry.data.get(CONF_INSTRUCTIONS))

        # Model name stays the same
        self._model = "gpt-4o-mini-tts"

    async def get_tts_audio(self, text: str, options: dict | None = None):
        """Generate TTS audio from GPT-4o using direct HTTP calls."""
        if options is None:
            options = {}

        # Allow per‑call overrides, else use our stored defaults
        voice = options.get("voice", self._voice)
        instructions = options.get("instructions", self._instructions)
        audio_format = options.get("audio_output", "mp3")
        speed = float(options.get(CONF_SPEED, DEFAULT_SPEED))
        # Ensure the API's allowed range 0.25-4.0
        speed = max(0.25, min(4.0, speed))

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "voice": voice,
            "input": text,
            "instructions": instructions,
            "response_format": audio_format,
            "speed": speed,
        }

        def do_request():
            resp = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload,
                stream=True,
            )
            resp.raise_for_status()

            # Collect the full audio stream
            audio_data = b""
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    audio_data += chunk
            return audio_format, audio_data

        try:
            return await self.hass.async_add_executor_job(do_request)
        except Exception as e:
            _LOGGER.error("Error generating GPT-4o TTS audio: %s", e)
            return None, None
