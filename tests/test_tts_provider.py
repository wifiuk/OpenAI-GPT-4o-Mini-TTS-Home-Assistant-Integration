import os
import sys
import types
import importlib
from dataclasses import dataclass
from collections.abc import AsyncGenerator
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Stub minimal Home Assistant modules required for import
ha = types.ModuleType("homeassistant")
ha.__path__ = []
ha.components = types.ModuleType("components")
ha.components.__path__ = []
ha.components.tts = types.ModuleType("tts")
ha.components.tts.__package__ = "homeassistant.components"
ha.components.tts.__path__ = []
ha.components.tts.TextToSpeechEntity = object
ha.components.tts.ATTR_AUDIO_OUTPUT = "audio_output"
ha.components.tts.ATTR_VOICE = "voice"
ha.components.tts.Voice = object
ha.components.tts.TtsAudioType = tuple[str | None, bytes | None]

ha.config_entries = types.ModuleType("config_entries")
ha.core = types.ModuleType("core")
ha.helpers = types.ModuleType("helpers")
ha.helpers.entity_platform = types.ModuleType("entity_platform")
ha.exceptions = types.ModuleType("exceptions")

# Basic attributes used in tts provider
@dataclass
class TTSAudioRequest:
    language: str
    options: dict
    message_gen: AsyncGenerator[str]

@dataclass
class TTSAudioResponse:
    extension: str
    data_gen: AsyncGenerator[bytes]

ha.components.tts.TTSAudioRequest = TTSAudioRequest
ha.components.tts.TTSAudioResponse = TTSAudioResponse
ha.components.tts.TextToSpeechEntity = object

class HomeAssistantError(Exception):
    pass
ha.exceptions.HomeAssistantError = HomeAssistantError

ha.config_entries.ConfigEntry = object
ha.core.HomeAssistant = object
ha.helpers.entity_platform.AddEntitiesCallback = object

sys.modules["homeassistant"] = ha
sys.modules["homeassistant.components"] = ha.components
sys.modules["homeassistant.components.tts"] = ha.components.tts
sys.modules["homeassistant.config_entries"] = ha.config_entries
sys.modules["homeassistant.core"] = ha.core
sys.modules["homeassistant.helpers"] = ha.helpers
sys.modules["homeassistant.helpers.entity_platform"] = ha.helpers.entity_platform
sys.modules["homeassistant.exceptions"] = ha.exceptions

sys.path.insert(0, BASE_DIR)

# Import after stubs are in place
tts_module = importlib.import_module("custom_components.openai_gpt4o_tts.tts")


class DummyEntry:
    def __init__(self):
        self.entry_id = "id"


class DummyClient:
    def __init__(self, stream_format="audio"):
        self.stream_format = stream_format
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

