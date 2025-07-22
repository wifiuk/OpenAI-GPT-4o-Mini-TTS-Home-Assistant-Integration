import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .gpt4o import GPT4oClient


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GPT-4o TTS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize the GPT-4o TTS client
    hass.data[DOMAIN][entry.entry_id] = GPT4oClient(hass, entry)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Forward to TTS platform so HA creates 'tts.openai_gpt4o_tts_say'
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GPT-4o TTS config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
