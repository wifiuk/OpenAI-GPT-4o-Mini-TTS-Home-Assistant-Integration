import logging
import requests

_LOGGER = logging.getLogger(__name__)

class GPT4oClient:
    """Handles direct calls to OpenAI's /v1/audio/speech for GPT-4o TTS."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        self._api_key = entry.data["api_key"]
        self._voice = entry.data.get("voice")
        # This single field now contains the combined instructions
        self._instructions = entry.data.get("instructions")
        self._model = "gpt-4o-mini-tts"

    async def get_tts_audio(self, text: str, options: dict | None = None):
        """Generate TTS audio from GPT-4o using direct HTTP calls."""
        if options is None:
            options = {}

        voice = options.get("voice", self._voice)
        instructions = options.get("instructions", self._instructions)
        audio_format = options.get("audio_output", "mp3")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model,
            "voice": voice,
            "input": text,
            "instructions": instructions,
            "response_format": audio_format
        }

        def do_request():
            resp = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload,
                stream=True
            )
            resp.raise_for_status()

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
