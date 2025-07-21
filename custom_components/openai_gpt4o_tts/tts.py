import logging
from typing import AsyncGenerator

from homeassistant.components.tts import (
    ATTR_AUDIO_OUTPUT,
    ATTR_VOICE,
    TtsAudioType,
    Voice,
)
from homeassistant.components.tts.entity import (
    TTSAudioRequest,
    TTSAudioResponse,
    TextToSpeechEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, OPENAI_TTS_VOICES, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from .gpt4o import GPT4oClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GPT‑4o TTS from a config entry."""
    client = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([OpenAIGPT4oTTSProvider(config_entry, client)])


class OpenAIGPT4oTTSProvider(TextToSpeechEntity):
    """GPT‑4o TTS => 'tts.openai_gpt4o_tts_say' in Developer Tools."""

    def __init__(self, config_entry: ConfigEntry, client: GPT4oClient) -> None:
        self._config_entry = config_entry
        self._client = client
        self._name = "OpenAI GPT‑4o Mini TTS"
        self._attr_unique_id = f"{config_entry.entry_id}-tts"

    @property
    def name(self) -> str:
        """Friendly name for the entity listing."""
        return self._name

    @property
    def default_language(self) -> str:
        """Return the default language code."""
        return DEFAULT_LANGUAGE

    @property
    def supported_languages(self) -> list[str]:
        """Return the full list of Whisper‑level language codes."""
        return SUPPORTED_LANGUAGES

    @property
    def default_options(self) -> dict:
        """Default TTS options, e.g. mp3."""
        return {ATTR_AUDIO_OUTPUT: "mp3"}

    @property
    def supported_options(self) -> list[str]:
        """Which TTS options can be overridden in the UI or service call."""
        return [ATTR_VOICE, "instructions", ATTR_AUDIO_OUTPUT]

    async def async_stream_tts_audio(
        self, request: TTSAudioRequest
    ) -> TTSAudioResponse:
        """Stream TTS audio or fall back to non-streaming."""
        options = dict(request.options or {})
        stream_enabled = options.pop("stream", True)
        message = "".join([chunk async for chunk in request.message_gen])

        if not stream_enabled:
            ext, data = await self.async_get_tts_audio(
                message, request.language, options
            )

            async def data_gen() -> AsyncGenerator[bytes, None]:
                if data:
                    yield data

            return TTSAudioResponse(ext or "mp3", data_gen())

        async def data_gen() -> AsyncGenerator[bytes, None]:
            async for chunk in self._client.iter_tts_audio(message, options):
                yield chunk

        audio_format = options.get(ATTR_AUDIO_OUTPUT, "mp3")
        return TTSAudioResponse(audio_format, data_gen())

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict | None = None
    ) -> TtsAudioType:
        """Called by Home Assistant to produce audio from text."""
        audio_format, audio_data = await self._client.get_tts_audio(message, options)
        if not audio_data:
            return None, None
        return audio_format, audio_data

    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return known GPT‑4o voices for the voice dropdown."""
        return [Voice(vid, vid.capitalize()) for vid in OPENAI_TTS_VOICES]

    @property
    def extra_state_attributes(self) -> dict:
        """Optional: expose provider name or debug info."""
        return {"provider": self._name}
