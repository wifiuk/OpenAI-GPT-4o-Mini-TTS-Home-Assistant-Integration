import os
import sys
import importlib
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from hass_stubs import install_homeassistant_stubs

install_homeassistant_stubs()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
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
