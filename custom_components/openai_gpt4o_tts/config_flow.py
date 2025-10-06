import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_PROVIDER,
    CONF_AZURE_ENDPOINT,
    CONF_VOICE,
    CONF_INSTRUCTIONS,
    CONF_LANGUAGE,
    PROVIDER_OPENAI,
    PROVIDER_AZURE,
    DEFAULT_PROVIDER,
    DEFAULT_VOICE,
    DEFAULT_LANGUAGE,
    DEFAULT_AFFECT,
    DEFAULT_TONE,
    DEFAULT_PRONUNCIATION,
    DEFAULT_PAUSE,
    DEFAULT_EMOTION,
    OPENAI_TTS_VOICES,
    SUPPORTED_LANGUAGES,
    OPENAI_TTS_MODELS,
    OPENAI_AUDIO_FORMATS,
    OPENAI_STREAM_FORMATS,
    CONF_PLAYBACK_SPEED,
    DEFAULT_PLAYBACK_SPEED,
    CONF_MODEL,
    CONF_AUDIO_OUTPUT,
    CONF_STREAM_FORMAT,
    DEFAULT_MODEL,
    DEFAULT_AUDIO_OUTPUT,
    DEFAULT_STREAM_FORMAT,
    CONF_VOLUME_GAIN,
    DEFAULT_VOLUME_GAIN,
    VOLUME_GAIN_MIN,
    VOLUME_GAIN_MAX,
)

_LOGGER = logging.getLogger(__name__)

class OpenAIGPT4oConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle OpenAI GPT‑4o Mini TTS setup flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._provider = None

    async def async_step_user(self, user_input=None):
        """Handle provider selection step."""
        errors = {}

        if user_input is not None:
            self._provider = user_input[CONF_PROVIDER]
            return await self.async_step_configure()

        # Show provider selection form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(
                    {PROVIDER_OPENAI: "OpenAI", PROVIDER_AZURE: "Azure AI Foundry"}
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_configure(self, user_input=None):
        """Handle provider-specific configuration (unified for both OpenAI and Azure)."""
        errors = {}

        if user_input is not None:
            # Validate Azure endpoint if Azure provider
            if self._provider == PROVIDER_AZURE:
                azure_endpoint = user_input.get(CONF_AZURE_ENDPOINT, "").strip()
                if not azure_endpoint:
                    errors["azure_endpoint"] = "Azure endpoint URL is required"
                elif not azure_endpoint.startswith("https://"):
                    errors["azure_endpoint"] = "Azure endpoint must start with https://"
                
                if errors:
                    # Re-show form with errors
                    pass
                else:
                    return await self._create_entry(user_input, self._provider, azure_endpoint)
            else:
                # OpenAI - no additional validation needed
                return await self._create_entry(user_input, self._provider)

        # Build schema dynamically based on provider
        schema_fields = {}
        
        # Add provider-specific fields first
        if self._provider == PROVIDER_AZURE:
            schema_fields[vol.Required(CONF_AZURE_ENDPOINT)] = str
            schema_fields[vol.Required(CONF_API_KEY)] = str
        else:
            schema_fields[vol.Required(CONF_API_KEY)] = str
        
        # Add common fields
        schema_fields.update({
            vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): vol.In(OPENAI_TTS_VOICES),
            vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(SUPPORTED_LANGUAGES),
            vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): vol.In(OPENAI_TTS_MODELS),
            vol.Optional(CONF_AUDIO_OUTPUT, default=DEFAULT_AUDIO_OUTPUT): vol.In(OPENAI_AUDIO_FORMATS),
            vol.Optional(CONF_STREAM_FORMAT, default=DEFAULT_STREAM_FORMAT): vol.In(OPENAI_STREAM_FORMATS),
            vol.Optional(CONF_PLAYBACK_SPEED, default=DEFAULT_PLAYBACK_SPEED): vol.All(
                vol.Coerce(float), vol.Range(min=0.25, max=4.0)
            ),
            vol.Optional(CONF_VOLUME_GAIN, default=DEFAULT_VOLUME_GAIN): vol.All(
                vol.Coerce(float), vol.Range(min=VOLUME_GAIN_MIN, max=VOLUME_GAIN_MAX)
            ),
            vol.Optional("affect_personality", default=DEFAULT_AFFECT): vol.All(
                str, vol.Length(min=5, max=500)
            ),
            vol.Optional("tone", default=DEFAULT_TONE): vol.All(
                str, vol.Length(min=5, max=500)
            ),
            vol.Optional("pronunciation", default=DEFAULT_PRONUNCIATION): vol.All(
                str, vol.Length(min=5, max=500)
            ),
            vol.Optional("pause", default=DEFAULT_PAUSE): vol.All(
                str, vol.Length(min=5, max=500)
            ),
            vol.Optional("emotion", default=DEFAULT_EMOTION): vol.All(
                str, vol.Length(min=5, max=500)
            ),
        })

        data_schema = vol.Schema(schema_fields)

        return self.async_show_form(
            step_id="configure", data_schema=data_schema, errors=errors
        )

    async def _create_entry(self, user_input, provider, azure_endpoint=None):
        """Create the config entry with the provided data."""
        # Combine the user's multi‑field instructions
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
        api_key = user_input[CONF_API_KEY].strip()
        data = {
            CONF_API_KEY: api_key,
            CONF_PROVIDER: provider,
        }
        
        # Add Azure endpoint to data if Azure provider
        if provider == PROVIDER_AZURE and azure_endpoint:
            data[CONF_AZURE_ENDPOINT] = azure_endpoint
            
        options = {
            CONF_VOICE: user_input.get(CONF_VOICE, DEFAULT_VOICE),
            CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            CONF_INSTRUCTIONS: user_input.get(CONF_INSTRUCTIONS, ""),
            CONF_MODEL: user_input.get(CONF_MODEL, DEFAULT_MODEL),
            CONF_AUDIO_OUTPUT: user_input.get(CONF_AUDIO_OUTPUT, DEFAULT_AUDIO_OUTPUT),
            CONF_STREAM_FORMAT: user_input.get(CONF_STREAM_FORMAT, DEFAULT_STREAM_FORMAT),
            CONF_PLAYBACK_SPEED: float(
                user_input.get(CONF_PLAYBACK_SPEED, DEFAULT_PLAYBACK_SPEED)
            ),
            CONF_VOLUME_GAIN: float(
                user_input.get(CONF_VOLUME_GAIN, DEFAULT_VOLUME_GAIN)
            ),
            "affect_personality": affect,
            "tone": tone,
            "pronunciation": pron,
            "pause": pause,
            "emotion": emo,
        }

        _LOGGER.debug("Creating entry with options: %s", options)
        title = "Azure OpenAI GPT-4o TTS" if provider == PROVIDER_AZURE else "OpenAI GPT-4o TTS"
        return self.async_create_entry(
            title=title, data=data, options=options
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
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_VOICE, default=existing.get(CONF_VOICE, DEFAULT_VOICE)
                ): vol.In(OPENAI_TTS_VOICES),
                vol.Optional(
                    CONF_LANGUAGE, default=existing.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                ): vol.In(SUPPORTED_LANGUAGES),
                vol.Optional(
                    CONF_MODEL, default=existing.get(CONF_MODEL, DEFAULT_MODEL)
                ): vol.In(OPENAI_TTS_MODELS),
                vol.Optional(
                    CONF_AUDIO_OUTPUT,
                    default=existing.get(CONF_AUDIO_OUTPUT, DEFAULT_AUDIO_OUTPUT),
                ): vol.In(OPENAI_AUDIO_FORMATS),
                vol.Optional(
                    CONF_STREAM_FORMAT,
                    default=existing.get(CONF_STREAM_FORMAT, DEFAULT_STREAM_FORMAT),
                ): vol.In(OPENAI_STREAM_FORMATS),
                vol.Optional(
                    CONF_PLAYBACK_SPEED,
                    default=existing.get(CONF_PLAYBACK_SPEED, DEFAULT_PLAYBACK_SPEED),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.25, max=4.0)),
                vol.Optional(
                    CONF_VOLUME_GAIN,
                    default=existing.get(CONF_VOLUME_GAIN, DEFAULT_VOLUME_GAIN),
                ): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=VOLUME_GAIN_MIN, max=VOLUME_GAIN_MAX),
                ),
                vol.Optional(
                    "affect_personality",
                    default=existing.get("affect_personality", DEFAULT_AFFECT),
                ): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional(
                    "tone", default=existing.get("tone", DEFAULT_TONE)
                ): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional(
                    "pronunciation",
                    default=existing.get("pronunciation", DEFAULT_PRONUNCIATION),
                ): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional(
                    "pause", default=existing.get("pause", DEFAULT_PAUSE)
                ): vol.All(str, vol.Length(min=5, max=500)),
                vol.Optional(
                    "emotion", default=existing.get("emotion", DEFAULT_EMOTION)
                ): vol.All(str, vol.Length(min=5, max=500)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
