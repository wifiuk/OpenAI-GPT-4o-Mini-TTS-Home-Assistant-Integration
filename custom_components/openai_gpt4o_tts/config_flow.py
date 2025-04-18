import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_VOICE,
    CONF_INSTRUCTIONS,
    CONF_LANGUAGE,
    DEFAULT_VOICE,
    DEFAULT_AFFECT,
    DEFAULT_TONE,
    DEFAULT_PRONUNCIATION,
    DEFAULT_PAUSE,
    DEFAULT_EMOTION,
    DEFAULT_LANGUAGE,
    OPENAI_TTS_VOICES,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


class OpenAIGPT4oConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenAI GPT‑4o TTS."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Initial step for user setup."""
        if user_input is not None:
            data = {CONF_API_KEY: user_input[CONF_API_KEY]}
            options = {
                CONF_VOICE: user_input.get(CONF_VOICE, DEFAULT_VOICE),
                CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                CONF_INSTRUCTIONS: user_input.get(CONF_INSTRUCTIONS),
                "affect_personality": user_input.get("affect_personality"),
                "tone": user_input.get("tone"),
                "pronunciation": user_input.get("pronunciation"),
                "pause": user_input.get("pause"),
                "emotion": user_input.get("emotion"),
            }
            return self.async_create_entry(
                title="OpenAI GPT‑4o TTS", data=data, options=options
            )

        existing = self.config_entry.options if self.config_entry else {}
        defaults = {
            CONF_VOICE: existing.get(CONF_VOICE, DEFAULT_VOICE),
            CONF_LANGUAGE: existing.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            CONF_INSTRUCTIONS: existing.get(CONF_INSTRUCTIONS, ""),
            "affect_personality": existing.get("affect_personality", DEFAULT_AFFECT),
            "tone": existing.get("tone", DEFAULT_TONE),
            "pronunciation": existing.get("pronunciation", DEFAULT_PRONUNCIATION),
            "pause": existing.get("pause", DEFAULT_PAUSE),
            "emotion": existing.get("emotion", DEFAULT_EMOTION),
        }

        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_VOICE, default=defaults[CONF_VOICE]): vol.In(OPENAI_TTS_VOICES),
            vol.Optional(CONF_LANGUAGE, default=defaults[CONF_LANGUAGE]): vol.In(SUPPORTED_LANGUAGES),
            vol.Optional(CONF_INSTRUCTIONS, default=defaults[CONF_INSTRUCTIONS]): str,
            vol.Optional("affect_personality", default=defaults["affect_personality"]): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("tone", default=defaults["tone"]): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("pronunciation", default=defaults["pronunciation"]): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("pause", default=defaults["pause"]): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("emotion", default=defaults["emotion"]): vol.All(str, vol.Length(min=5, max=500)),
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OpenAIGPT4oOptionsFlowHandler(config_entry)


class OpenAIGPT4oOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle GPT‑4o TTS options flow."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await OpenAIGPT4oConfigFlow.async_step_user(self, user_input)
