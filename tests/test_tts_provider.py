import os
import sys
import importlib
from collections.abc import AsyncGenerator

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from hass_stubs import install_homeassistant_stubs

install_homeassistant_stubs()

from homeassistant.components.tts import TTSAudioRequest  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

# Import after stubs are in place
tts_module = importlib.import_module("custom_components.openai_gpt4o_tts.tts")
const = importlib.import_module("custom_components.openai_gpt4o_tts.const")


class DummyEntry:
    def __init__(self):
        self.entry_id = "id"


class DummyClient:
    def __init__(self, stream_format="audio"):
        self.stream_format = stream_format
        self.audio_output = "mp3"
        self.called = []

    async def get_tts_audio(self, message, options=None):
        self.called.append(("get", message, options))
        return "mp3", b"joined"

    async def stream_tts_audio(self, message, options=None):
        self.called.append(("stream", message, options))

        async def gen():
            yield b"a"
            yield b"b"

        return "mp3", gen()


async def _gen_message(text: str) -> AsyncGenerator[str]:
    yield text


@pytest.mark.asyncio
async def test_stream_method_non_sse():
    client = DummyClient()
    provider = tts_module.OpenAIGPT4oTTSProvider(DummyEntry(), client)
    req = TTSAudioRequest("en", {"stream_format": "audio"}, _gen_message("hi"))
    resp = await provider.async_stream_tts_audio(req)
    data = b"".join([chunk async for chunk in resp.data_gen])
    assert resp.extension == "mp3"
    assert data == b"joined"
    assert client.called[0][0] == "get"


@pytest.mark.asyncio
async def test_stream_method_sse():
    client = DummyClient()
    provider = tts_module.OpenAIGPT4oTTSProvider(DummyEntry(), client)
    req = TTSAudioRequest("en", {"stream_format": "sse"}, _gen_message("hi"))
    resp = await provider.async_stream_tts_audio(req)
    data = b"".join([chunk async for chunk in resp.data_gen])
    assert resp.extension == "mp3"
    assert data == b"ab"
    assert client.called[0][0] == "stream"


def test_default_and_supported_options():
    client = DummyClient()
    provider = tts_module.OpenAIGPT4oTTSProvider(DummyEntry(), client)
    assert const.CONF_VOLUME_GAIN in provider.supported_options
    assert provider.default_options[const.CONF_VOLUME_GAIN] == const.DEFAULT_VOLUME_GAIN
