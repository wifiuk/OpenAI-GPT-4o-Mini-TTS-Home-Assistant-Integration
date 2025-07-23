from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from collections.abc import AsyncGenerator


def install_homeassistant_stubs() -> None:
    """Install minimal Home Assistant module stubs for unit tests."""
    if "homeassistant" in sys.modules:
        return

    ha = types.ModuleType("homeassistant")
    ha.__path__ = []

    ha.components = types.ModuleType("components")
    ha.components.__path__ = []
    tts = types.ModuleType("tts")
    tts.__package__ = "homeassistant.components"
    tts.__path__ = []
    tts.TextToSpeechEntity = object
    tts.ATTR_AUDIO_OUTPUT = "audio_output"
    tts.ATTR_VOICE = "voice"
    tts.Voice = object
    tts.TtsAudioType = tuple[str | None, bytes | None]

    @dataclass
    class TTSAudioRequest:
        language: str
        options: dict
        message_gen: AsyncGenerator[str, None]

    @dataclass
    class TTSAudioResponse:
        extension: str
        data_gen: AsyncGenerator[bytes, None]

    tts.TTSAudioRequest = TTSAudioRequest
    tts.TTSAudioResponse = TTSAudioResponse

    ha.components.tts = tts

    ha.config_entries = types.ModuleType("config_entries")
    ha.config_entries.CONN_CLASS_CLOUD_POLL = "cloud_poll"

    class _BaseConfigFlow:
        def __init_subclass__(cls, *args, domain=None, **kwargs):
            super().__init_subclass__(*args, **kwargs)
            cls.domain = domain

        def async_show_form(self, **kwargs):
            return kwargs

        def async_create_entry(self, **kwargs):
            self.created_entry = kwargs
            return kwargs

    ha.config_entries.ConfigFlow = _BaseConfigFlow
    ha.config_entries.OptionsFlow = object
    ha.config_entries.ConfigEntry = object

    ha.core = types.ModuleType("core")
    ha.core.HomeAssistant = object
    ha.core.callback = lambda func: func

    ha.helpers = types.ModuleType("helpers")
    ha.helpers.entity_platform = types.ModuleType("entity_platform")
    ha.helpers.entity_platform.AddEntitiesCallback = object

    ha.exceptions = types.ModuleType("exceptions")

    class HomeAssistantError(Exception):
        """Basic Home Assistant error for tests."""

    ha.exceptions.HomeAssistantError = HomeAssistantError

    ha.const = types.ModuleType("const")
    ha.const.CONF_API_KEY = "api_key"

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.components"] = ha.components
    sys.modules["homeassistant.components.tts"] = tts
    sys.modules["homeassistant.config_entries"] = ha.config_entries
    sys.modules["homeassistant.core"] = ha.core
    sys.modules["homeassistant.helpers"] = ha.helpers
    sys.modules["homeassistant.helpers.entity_platform"] = ha.helpers.entity_platform
    sys.modules["homeassistant.exceptions"] = ha.exceptions
    sys.modules["homeassistant.const"] = ha.const
