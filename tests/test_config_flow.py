import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from hass_stubs import install_homeassistant_stubs

install_homeassistant_stubs()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

cfg_flow = importlib.import_module("custom_components.openai_gpt4o_tts.config_flow")
gpt4o = importlib.import_module("custom_components.openai_gpt4o_tts.gpt4o")
OpenAIGPT4oConfigFlow = cfg_flow.OpenAIGPT4oConfigFlow
GPT4oClient = gpt4o.GPT4oClient


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
        self.headers = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def post(self, url, headers=None, json=None):
        self.payload = json
        self.headers = headers
        return DummyResponse()


@pytest.mark.asyncio
async def test_api_key_whitespace(monkeypatch):
    flow = OpenAIGPT4oConfigFlow()
    result = await flow.async_step_user({"api_key": "  k  "})
    assert result["data"]["api_key"] == "k"

    entry = DummyEntry(data=result["data"])
    client = GPT4oClient(None, entry)

    dummy = DummySession()
    monkeypatch.setattr(
        "custom_components.openai_gpt4o_tts.gpt4o.ClientSession",
        lambda timeout=None: dummy,
    )

    fmt, data = await client.get_tts_audio("hi")
    assert fmt == "mp3"
    assert dummy.headers["Authorization"] == "Bearer k"
    assert dummy.payload["model"] == gpt4o.DEFAULT_MODEL
    assert dummy.payload["response_format"] == gpt4o.DEFAULT_AUDIO_OUTPUT
    assert dummy.payload["stream_format"] == gpt4o.DEFAULT_STREAM_FORMAT


@pytest.mark.asyncio
async def test_stream_format_option():
    flow = OpenAIGPT4oConfigFlow()
    result = await flow.async_step_user(
        {"api_key": "k", gpt4o.CONF_STREAM_FORMAT: "sse"}
    )
    assert result["options"][gpt4o.CONF_STREAM_FORMAT] == "sse"
