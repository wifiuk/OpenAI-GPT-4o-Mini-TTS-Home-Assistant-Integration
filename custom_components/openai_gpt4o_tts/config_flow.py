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
    DEFAULT_LANGUAGE,
    CONF_SPEED,
    DEFAULT_SPEED,
    DEFAULT_AFFECT,
    DEFAULT_TONE,
    DEFAULT_PRONUNCIATION,
    DEFAULT_PAUSE,
    DEFAULT_EMOTION,
    OPENAI_TTS_VOICES,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


class OpenAIGPT4oConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle OpenAI GPT‑4o Mini TTS setup flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None, errors=None):
        """Initial configuration step."""
        errors = errors or {}

        if user_input is not None:
            # Combine the user’s multi‑field instructions exactly as before
            affect = user_input.get("affect_personality", "")
            tone = user_input.get("tone", "")
            pron = user_input.get("pronunciation", "")
            pause = user_input.get("pause", "")
            emo = user_input.get("emotion", "")

            parts = []
            if affect:
                parts.append(f"Affect/personality: {affect}")
            if tone:
                parts.append(f"Tone: {tone}")
            if pron:
                parts.append(f"Pronunciation: {pron}")
            if pause:
                parts.append(f"Pause: {pause}")
            if emo:
                parts.append(f"Emotion: {emo}")

            user_input[CONF_INSTRUCTIONS] = "\n".join(parts)

            # Build data + options dicts
            data = {CONF_API_KEY: user_input[CONF_API_KEY]}
            options = {
                CONF_VOICE: user_input.get(CONF_VOICE, DEFAULT_VOICE),
                CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                CONF_SPEED: user_input.get(CONF_SPEED, DEFAULT_SPEED),
                CONF_INSTRUCTIONS: user_input.get(CONF_INSTRUCTIONS, ""),
                "affect_personality": affect,
                "tone": tone,
                "pronunciation": pron,
                "pause": pause,
                "emotion": emo,
            }

            _LOGGER.debug("Creating entry with options: %s", options)
            return self.async_create_entry(title="OpenAI GPT‑4o TTS", data=data, options=options)

        # Show the setup form
        data_schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(OPENAI_TTS_VOICES),
            vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(SUPPORTED_LANGUAGES),
            vol.Optional(CONF_SPEED, default=DEFAULT_SPEED): vol.All(
                vol.Coerce(float), vol.Range(min=0.25, max=4.0)
            ),
            vol.Optional("affect_personality", default=DEFAULT_AFFECT): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("tone", default=DEFAULT_TONE): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("pronunciation", default=DEFAULT_PRONUNCIATION): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("pause", default=DEFAULT_PAUSE): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("emotion", default=DEFAULT_EMOTION): vol.All(str, vol.Length(min=5, max=500)),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Allow the user to re‑configure later."""
        return OpenAIGPT4oOptionsFlowHandler(config_entry)


class OpenAIGPT4oOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing existing TTS settings."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Store config entry without using deprecated property."""
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show the options form with pre‑filled values."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        existing = self._entry.options or self._entry.data
        data_schema = vol.Schema({
            vol.Optional(CONF_VOICE, default=existing.get(CONF_VOICE, DEFAULT_VOICE)): vol.In(OPENAI_TTS_VOICES),
            vol.Optional(CONF_LANGUAGE, default=existing.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)): vol.In(SUPPORTED_LANGUAGES),
            vol.Optional(CONF_SPEED, default=existing.get(CONF_SPEED, DEFAULT_SPEED)): vol.All(
                vol.Coerce(float), vol.Range(min=0.25, max=4.0)
            ),
            vol.Optional("affect_personality", default=existing.get("affect_personality", DEFAULT_AFFECT)): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("tone", default=existing.get("tone", DEFAULT_TONE)): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("pronunciation", default=existing.get("pronunciation", DEFAULT_PRONUNCIATION)): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("pause", default=existing.get("pause", DEFAULT_PAUSE)): vol.All(str, vol.Length(min=5, max=500)),
            vol.Optional("emotion", default=existing.get("emotion", DEFAULT_EMOTION)): vol.All(str, vol.Length(min=5, max=500)),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema
        )
