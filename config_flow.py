import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback

from .const import (
    DOMAIN,
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
    VERSION = 1

    async def async_step_user(self, user_input=None):
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
            user_input["instructions"] = combined_instructions

            _LOGGER.debug(
                "Creating config entry with combined instructions:\n%s",
                combined_instructions
            )

            return self.async_create_entry(title="OpenAI GPT-4o Mini TTS", data=user_input)

        # Show the form for the first time
        data_schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional("voice", default=DEFAULT_VOICE): vol.In(OPENAI_TTS_VOICES),

            # Each “instructions” field has its own default
            vol.Optional("affect_personality", default=DEFAULT_AFFECT): str,
            vol.Optional("tone", default=DEFAULT_TONE): str,
            vol.Optional("pronunciation", default=DEFAULT_PRONUNCIATION): str,
            vol.Optional("pause", default=DEFAULT_PAUSE): str,
            vol.Optional("emotion", default=DEFAULT_EMOTION): str,
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
    """Optional flow to edit instructions after initial setup."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Could re-build instructions if you want to let them edit each field
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
