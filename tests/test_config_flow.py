import os
import sys
import importlib

import pytest
import voluptuous as vol

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


async def _start_flow(flow: OpenAIGPT4oConfigFlow):
    await flow.async_step_user({gpt4o.CONF_PROVIDER: gpt4o.DEFAULT_PROVIDER})


@pytest.mark.asyncio
async def test_volume_gain_persisted_and_trimmed_api_key(monkeypatch):
    flow = OpenAIGPT4oConfigFlow()
    await _start_flow(flow)

    result = await flow.async_step_configure(
        {
            "api_key": "  k  ",
            gpt4o.CONF_VOLUME_GAIN: 1.5,
        }
    )

    assert result["data"]["api_key"] == "k"
    assert pytest.approx(result["options"][gpt4o.CONF_VOLUME_GAIN]) == 1.5

    entry = DummyEntry(data=result["data"], options=result["options"])
    client = GPT4oClient(None, entry)

    dummy = DummySession()
    monkeypatch.setattr(
        "custom_components.openai_gpt4o_tts.gpt4o.ClientSession",
        lambda timeout=None: dummy,
    )

    fmt, data = await client.get_tts_audio("hi")
    assert fmt == result["options"][gpt4o.CONF_AUDIO_OUTPUT]
    assert dummy.headers["Authorization"] == "Bearer k"
    assert dummy.payload["model"] == gpt4o.DEFAULT_MODEL
    assert dummy.payload["response_format"] == gpt4o.DEFAULT_AUDIO_OUTPUT
    assert dummy.payload["stream_format"] == gpt4o.DEFAULT_STREAM_FORMAT


@pytest.mark.asyncio
async def test_volume_gain_schema_bounds():
    flow = OpenAIGPT4oConfigFlow()
    await _start_flow(flow)
    form = await flow.async_step_configure()
    schema = form["data_schema"]

    with pytest.raises(vol.Invalid):
        schema({"api_key": "k", gpt4o.CONF_VOLUME_GAIN: 0.05})

    with pytest.raises(vol.Invalid):
        schema({"api_key": "k", gpt4o.CONF_VOLUME_GAIN: 5.0})


@pytest.mark.asyncio
async def test_stream_format_option():
    flow = OpenAIGPT4oConfigFlow()
    await _start_flow(flow)
    result = await flow.async_step_configure(
        {
            "api_key": "k",
            gpt4o.CONF_STREAM_FORMAT: "sse",
        }
    )
    assert result["options"][gpt4o.CONF_STREAM_FORMAT] == "sse"
