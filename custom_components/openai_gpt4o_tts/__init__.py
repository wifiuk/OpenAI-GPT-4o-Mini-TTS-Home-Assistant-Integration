import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .gpt4o import GPT4oClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GPT-4o TTS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store the config entry so it persists
    hass.data[DOMAIN][entry.entry_id] = entry

    # Initialize the GPT-4o TTS client
    hass.data[DOMAIN][entry.entry_id] = GPT4oClient(hass, entry)

    # Forward to TTS platform so HA creates 'tts.openai_gpt4o_tts_say'
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GPT-4o TTS config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
