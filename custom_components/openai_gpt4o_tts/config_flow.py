import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_VOICE,
    CONF_INSTRUCTIONS,
    DEFAULT_VOICE,
    DEFAULT_AFFECT,
    DEFAULT_TONE,
    DEFAULT_PRONUNCIATION,
    DEFAULT_PAUSE,
    DEFAULT_EMOTION,
    OPENAI_TTS_VOICES
)

_LOGGER = logging.getLogger(__name__)

class OpenAITTSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle OpenAI GPT-4o Mini TTS setup flow."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial configuration step."""
        errors = {}

        if user_input is not None:
            # Combine the user’s multiple fields into a single instructions string
            affect_personality = user_input.get("affect_personality", "")
            tone = user_input.get("tone", "")
            pronunciation = user_input.get("pronunciation", "")
            pause = user_input.get("pause", "")
            emotion = user_input.get("emotion", "")

            instructions_parts = []
            if affect_personality:
                instructions_parts.append(f"Affect/personality: {affect_personality}")
            if tone:
                instructions_parts.append(f"Tone: {tone}")
            if pronunciation:
                instructions_parts.append(f"Pronunciation: {pronunciation}")
            if pause:
                instructions_parts.append(f"Pause: {pause}")
            if emotion:
                instructions_parts.append(f"Emotion: {emotion}")

            combined_instructions = "\n".join(instructions_parts)
            user_input[CONF_INSTRUCTIONS] = combined_instructions

            _LOGGER.debug(
                "Creating config entry with combined instructions:\n%s",
                combined_instructions
            )

            return self.async_create_entry(title="OpenAI GPT-4o Mini TTS", data=user_input)

        # Show the setup form
        data_schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(OPENAI_TTS_VOICES),
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
        return OpenAITTSOptionsFlowHandler(config_entry)


class OpenAITTSOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing OpenAI GPT-4o Mini TTS settings."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show the options form with pre-filled values."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Retrieve existing settings from config entry
        existing_settings = self.config_entry.options or self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_VOICE, default=existing_settings.get(CONF_VOICE, DEFAULT_VOICE)): vol.In(OPENAI_TTS_VOICES),
                vol.Optional("affect_personality", default=existing_settings.get("affect_personality", DEFAULT_AFFECT)): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional("tone", default=existing_settings.get("tone", DEFAULT_TONE)): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional("pronunciation", default=existing_settings.get("pronunciation", DEFAULT_PRONUNCIATION)): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional("pause", default=existing_settings.get("pause", DEFAULT_PAUSE)): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional("emotion", default=existing_settings.get("emotion", DEFAULT_EMOTION)): vol.All(str, vol.Length(min=5, max=500)),
            })
        )
