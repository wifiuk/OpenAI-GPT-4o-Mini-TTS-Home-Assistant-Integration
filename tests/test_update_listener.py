import os
import sys
import importlib
import types
from types import SimpleNamespace

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Stub minimal Home Assistant modules
ha = types.ModuleType("homeassistant")
ha.config_entries = types.ModuleType("config_entries")
ha.core = types.ModuleType("core")
ha.config_entries.ConfigEntry = object
ha.core.HomeAssistant = object
sys.modules.setdefault("homeassistant", ha)
sys.modules.setdefault("homeassistant.config_entries", ha.config_entries)
sys.modules.setdefault("homeassistant.core", ha.core)

sys.path.insert(0, BASE_DIR)
init = importlib.import_module("custom_components.openai_gpt4o_tts.__init__")


class DummyConfigEntries:
    def __init__(self):
        self.reloaded = None

    async def async_reload(self, entry_id):
        self.reloaded = entry_id


@pytest.mark.asyncio
async def test_update_listener_triggers_reload():
    hass = SimpleNamespace(config_entries=DummyConfigEntries())
    entry = SimpleNamespace(entry_id="abc")
    await init._async_update_listener(hass, entry)
    assert hass.config_entries.reloaded == "abc"
