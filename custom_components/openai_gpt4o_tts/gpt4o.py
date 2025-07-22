"""Client for OpenAI GPT-4o Mini TTS."""

import asyncio
import base64
import binascii
import json
import logging
import re
from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import (
    CONF_INSTRUCTIONS,
    CONF_PLAYBACK_SPEED,
    CONF_VOICE,
    CONF_MODEL,
    CONF_AUDIO_OUTPUT,
    CONF_STREAM_FORMAT,
    DEFAULT_PLAYBACK_SPEED,
    DEFAULT_VOICE,
    DEFAULT_MODEL,
    DEFAULT_AUDIO_OUTPUT,
    DEFAULT_STREAM_FORMAT,
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
        self._model = opts.get(
            CONF_MODEL, entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        )
        self._audio_output = opts.get(
            CONF_AUDIO_OUTPUT, entry.data.get(CONF_AUDIO_OUTPUT, DEFAULT_AUDIO_OUTPUT)
        )
        self._stream_format = opts.get(
            CONF_STREAM_FORMAT, entry.data.get(CONF_STREAM_FORMAT, DEFAULT_STREAM_FORMAT)
        )

    async def _iter_sse_audio(self, resp: ClientResponse):
        """Yield audio bytes from an SSE response."""
        buffer = ""
        async for raw in resp.content:
            line = raw.decode("utf-8")
            if line.startswith("data:"):
                data_part = line[5:].strip()
                if data_part == "[DONE]":
                    break
                buffer += data_part
            elif line.strip() == "":
                if not buffer:
                    continue
                try:
                    event = json.loads(buffer)
                except json.JSONDecodeError:
                    buffer = ""
                    continue
                buffer = ""
                if event.get("type") == "speech.audio.delta":
                    audio_b64 = event.get("audio", "")
                    if audio_b64:
                        try:
                            yield base64.b64decode(audio_b64)
                        except (binascii.Error, ValueError):
                            _LOGGER.warning("Invalid audio chunk in SSE stream")
                elif event.get("type") == "speech.audio.done":
                    break
        if buffer:
            try:
                event = json.loads(buffer)
                if event.get("type") == "speech.audio.delta":
                    audio_b64 = event.get("audio", "")
                    if audio_b64:
                        yield base64.b64decode(audio_b64)
            except json.JSONDecodeError:
                pass

    @property
    def audio_output(self) -> str:
        """Return the default audio output format."""
        return self._audio_output

    async def iter_tts_audio(self, text: str, options: dict | None = None):
        """Asynchronously yield audio chunks from the API."""
        if options is None:
            options = {}

        voice = options.get("voice", self._voice) or DEFAULT_VOICE
        instructions = options.get("instructions", self._instructions) or ""
        audio_format = options.get("audio_output", self._audio_output)
        model = options.get(CONF_MODEL, self._model)
        stream_format = options.get(CONF_STREAM_FORMAT, self._stream_format)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "instructions": instructions,
            "response_format": audio_format,
            "speed": float(options.get(CONF_PLAYBACK_SPEED, self._playback_speed)),
            "stream_format": stream_format,
        }

        timeout = ClientTimeout(total=REQUEST_TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            async with session.post(
                OPENAI_TTS_ENDPOINT,
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status >= 400:
                    await _log_api_error(resp)
                    return
                if stream_format == "sse":
                    async for chunk in self._iter_sse_audio(resp):
                        yield chunk
                else:
                    async for chunk in resp.content.iter_chunked(8192):
                        if chunk:
                            yield chunk

    async def get_tts_audio(self, text: str, options: dict | None = None):
        """Generate TTS audio from GPT-4o using direct HTTP calls."""
        try:
            audio_chunks = [chunk async for chunk in self.iter_tts_audio(text, options)]
            if not audio_chunks:
                return None, None
            audio_format = options.get("audio_output", self._audio_output) if options else self._audio_output
            return audio_format, b"".join(audio_chunks)
        except asyncio.TimeoutError:
            _LOGGER.error(
                "GPT-4o TTS request timed out after %s seconds", REQUEST_TIMEOUT
            )
        except ClientError as err:
            _LOGGER.error("Error generating GPT-4o TTS audio: %s", err)
        except Exception as err:  # pragma: no cover - unexpected errors
            _LOGGER.error("Unexpected error generating GPT-4o TTS audio: %s", err)
        return None, None
