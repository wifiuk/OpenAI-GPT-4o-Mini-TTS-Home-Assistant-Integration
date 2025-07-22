"""Client for OpenAI GPT-4o Mini TTS."""

import asyncio
import logging
import re
from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import (
    CONF_INSTRUCTIONS,
    CONF_PLAYBACK_SPEED,
    CONF_VOICE,
    DEFAULT_PLAYBACK_SPEED,
    DEFAULT_VOICE,
)

_LOGGER = logging.getLogger(__name__)

# Request timeout for the OpenAI API in seconds
REQUEST_TIMEOUT = 30

# API endpoint for speech generation
OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"

# Regex to detect API keys so they can be masked in logs. Keys may include
# prefixes like ``sk-proj-`` or ``sk-svcacct-`` so we allow hyphens in the
# character set and require a reasonable length to avoid false positives.
_API_KEY_RE = re.compile(r"sk-[A-Za-z0-9-]{16,}")


def _mask_api_keys(text: str) -> str:
    """Return ``text`` with API keys masked."""
    return _API_KEY_RE.sub("sk-***", text)


async def _log_api_error(resp: ClientResponse) -> None:
    """Log error details returned by the OpenAI API."""
    try:
        data = await resp.json()
        message = data.get("error", {}).get("message", str(data))
    except Exception:  # pragma: no cover - non-JSON error
        message = await resp.text()
    sanitized = _mask_api_keys(str(message))
    _LOGGER.error("OpenAI TTS API error %s: %s", resp.status, sanitized)


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
        self._playback_speed = float(
            opts.get(
                CONF_PLAYBACK_SPEED,
                entry.data.get(CONF_PLAYBACK_SPEED, DEFAULT_PLAYBACK_SPEED),
            )
        )

        # Model name stays the same
        self._model = "gpt-4o-mini-tts"

    async def get_tts_audio(self, text: str, options: dict | None = None):
        """Generate TTS audio from GPT-4o using direct HTTP calls."""
        if options is None:
            options = {}

        # Allow per‑call overrides, else use our stored defaults
        voice = options.get("voice", self._voice)
        if not voice:
            voice = DEFAULT_VOICE
        instructions = options.get("instructions", self._instructions)
        if instructions is None:
            instructions = ""
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
            "speed": float(options.get(CONF_PLAYBACK_SPEED, self._playback_speed)),
        }

        async def do_request() -> tuple[str | None, bytes | None]:
            """Send TTS request to OpenAI and return audio data."""
            timeout = ClientTimeout(total=REQUEST_TIMEOUT)
            async with ClientSession(timeout=timeout) as session:
                async with session.post(
                    OPENAI_TTS_ENDPOINT,
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status >= 400:
                        await _log_api_error(resp)
                        return None, None
                    audio_chunks = []
                    async for chunk in resp.content.iter_chunked(8192):
                        if chunk:
                            audio_chunks.append(chunk)
                    return audio_format, b"".join(audio_chunks)

        try:
            return await do_request()
        except asyncio.TimeoutError:
            _LOGGER.error(
                "GPT-4o TTS request timed out after %s seconds", REQUEST_TIMEOUT
            )
        except ClientError as err:
            _LOGGER.error("Error generating GPT-4o TTS audio: %s", err)
        except Exception as err:  # pragma: no cover - unexpected errors
            _LOGGER.error("Unexpected error generating GPT-4o TTS audio: %s", err)
        return None, None
