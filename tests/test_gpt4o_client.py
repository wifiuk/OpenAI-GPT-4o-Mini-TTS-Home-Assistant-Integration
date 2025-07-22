import asyncio
import os
import sys
import importlib.util
import types
from types import SimpleNamespace

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Stub minimal Home Assistant modules required for import
ha = types.ModuleType("homeassistant")
ha.config_entries = types.ModuleType("config_entries")
ha.core = types.ModuleType("core")
ha.helpers = types.ModuleType("helpers")
ha.helpers.entity_platform = types.ModuleType("entity_platform")
ha.components = types.ModuleType("components")
ha.components.tts = types.ModuleType("tts")
ha.config_entries.ConfigEntry = object
ha.core.HomeAssistant = object
sys.modules.setdefault("homeassistant", ha)
sys.modules.setdefault("homeassistant.config_entries", ha.config_entries)
sys.modules.setdefault("homeassistant.core", ha.core)
sys.modules.setdefault("homeassistant.helpers", ha.helpers)
sys.modules.setdefault("homeassistant.helpers.entity_platform", ha.helpers.entity_platform)
sys.modules.setdefault("homeassistant.components", ha.components)
sys.modules.setdefault("homeassistant.components.tts", ha.components.tts)

sys.path.insert(0, BASE_DIR)
gpt4o = importlib.import_module("custom_components.openai_gpt4o_tts.gpt4o")
GPT4oClient = gpt4o.GPT4oClient
DEFAULT_VOICE = gpt4o.DEFAULT_VOICE

class DummyEntry:
    def __init__(self, data=None, options=None):
        self.data = data or {}
        self.options = options or {}

class DummyContent:
    async def iter_chunked(self, size):
        yield b"audio"

class DummyResponse:
    def __init__(self):
        self.status = 200
        self.content = DummyContent()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def json(self):
        return {}

    async def text(self):
        return ""

class DummySession:
    def __init__(self, *args, **kwargs):
        self.payload = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def post(self, url, headers=None, json=None):
        self.payload = json
        return DummyResponse()

@pytest.mark.asyncio
async def test_instructions_default(monkeypatch):
    entry = DummyEntry(data={"api_key": "k"})
    client = GPT4oClient(None, entry)

    dummy = DummySession()
    monkeypatch.setattr("custom_components.openai_gpt4o_tts.gpt4o.ClientSession", lambda timeout=None: dummy)

    fmt, data = await client.get_tts_audio("hello")
    assert fmt == "mp3"
    assert dummy.payload["instructions"] == ""
    assert dummy.payload["voice"] == DEFAULT_VOICE


class ErrorResponse:
    def __init__(self, message: str, use_json: bool = True):
        self.status = 401
        self._message = message
        self.use_json = use_json

    async def json(self):
        if self.use_json:
            return {"error": {"message": self._message}}
        raise ValueError("no json")

    async def text(self):
        return self._message


@pytest.mark.asyncio
async def test_log_api_error_masks_api_key_json(caplog):
    key = "sk-1234567890ABCDEF"
    resp = ErrorResponse(f"invalid key {key}")
    with caplog.at_level("ERROR"):
        await gpt4o._log_api_error(resp)
    assert key not in caplog.text
    assert "sk-***" in caplog.text


@pytest.mark.asyncio
async def test_log_api_error_masks_api_key_text(caplog):
    key = "sk-ABCDEFG1234567890"
    resp = ErrorResponse(f"bad request {key}", use_json=False)
    with caplog.at_level("ERROR"):
        await gpt4o._log_api_error(resp)
    assert key not in caplog.text
    assert "sk-***" in caplog.text
