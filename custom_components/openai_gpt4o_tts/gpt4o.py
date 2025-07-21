import logging
from typing import AsyncGenerator
from requests import RequestException, Timeout, post

import aiohttp
import requests

from .const import CONF_VOICE, CONF_INSTRUCTIONS

API_URL = "https://api.openai.com/v1/audio/speech"

_LOGGER = logging.getLogger(__name__)

# Request timeout for the OpenAI API in seconds
REQUEST_TIMEOUT = 30


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
        self._instructions = opts.get(
            CONF_INSTRUCTIONS, entry.data.get(CONF_INSTRUCTIONS)
        )

        # Model name stays the same
        self._model = "gpt-4o-mini-tts"

    async def iter_tts_audio(
        self, text: str, options: dict | None = None
    ) -> AsyncGenerator[bytes, None]:
        """Yield audio chunks directly from the API."""
        if options is None:
            options = {}

        voice = options.get("voice", self._voice)
        instructions = options.get("instructions", self._instructions)
        audio_format = options.get("audio_output", "mp3")

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
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.content.iter_chunked(8192):
                        if chunk:
                            yield chunk
        except Exception as err:  # pragma: no cover - network errors
            _LOGGER.error("Error streaming GPT-4o TTS audio: %s", err)

    async def get_tts_audio(self, text: str, options: dict | None = None):
        """Generate TTS audio from GPT-4o using direct HTTP calls."""
        if options is None:
            options = {}

        # Allow per‑call overrides, else use our stored defaults
        voice = options.get("voice", self._voice)
        instructions = options.get("instructions", self._instructions)
        audio_format = options.get("audio_output", "mp3")

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
        }

        def do_request():
            resp = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=REQUEST_TIMEOUT,
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
        except Timeout:
            _LOGGER.error(
                "GPT-4o TTS request timed out after %s seconds", REQUEST_TIMEOUT
            )
            return None, None
        except RequestException as err:
            _LOGGER.error("Error generating GPT-4o TTS audio: %s", err)
            return None, None
        except Exception as err:  # pragma: no cover - unexpected errors
            _LOGGER.error("Unexpected error generating GPT-4o TTS audio: %s", err)
            return None, None
