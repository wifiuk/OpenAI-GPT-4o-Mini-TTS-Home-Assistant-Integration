import asyncio
import os
import sys
import importlib
import pytest
import struct

sys.path.insert(0, os.path.dirname(__file__))
from hass_stubs import install_homeassistant_stubs

install_homeassistant_stubs()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
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


class DummySSEContent:
    def __init__(self, lines):
        self.lines = lines

    def __aiter__(self):
        async def gen():
            for line in self.lines:
                for part in line.split(b"\n"):
                    yield (part + b"\n") if part else b"\n"

        return gen()


class DummySSEResponse:
    def __init__(self, lines):
        self.status = 200
        self.content = DummySSEContent(lines)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def json(self):
        return {}

    async def text(self):
        return ""


class DummySSESession:
    def __init__(self, lines):
        self.payload = None
        self.lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def post(self, url, headers=None, json=None):
        self.payload = json
        return DummySSEResponse(self.lines)


@pytest.mark.asyncio
async def test_instructions_default(monkeypatch):
    entry = DummyEntry(data={"api_key": "k"})
    client = GPT4oClient(None, entry)

    dummy = DummySession()
    monkeypatch.setattr(
        "custom_components.openai_gpt4o_tts.gpt4o.ClientSession",
        lambda timeout=None: dummy,
    )

    fmt, data = await client.get_tts_audio("hello")
    assert fmt == "mp3"
    assert dummy.payload["instructions"] == ""
    assert dummy.payload["voice"] == DEFAULT_VOICE
    assert dummy.payload["model"] == gpt4o.DEFAULT_MODEL
    assert dummy.payload["response_format"] == gpt4o.DEFAULT_AUDIO_OUTPUT
    assert dummy.payload["stream_format"] == gpt4o.DEFAULT_STREAM_FORMAT


@pytest.mark.asyncio
async def test_sse_stream(monkeypatch):
    entry = DummyEntry(data={"api_key": "k"})
    client = GPT4oClient(None, entry)

    lines = [
        b'data: {"type": "speech.audio.delta", "audio": "ZGF0YTE="}\n\n',
        b'data: {"type": "speech.audio.delta", "audio": "ZGF0YTI="}\n\n',
        b'data: {"type": "speech.audio.done"}\n\n',
    ]
    session = DummySSESession(lines)
    monkeypatch.setattr(
        "custom_components.openai_gpt4o_tts.gpt4o.ClientSession",
        lambda timeout=None: session,
    )

    fmt, data = await client.get_tts_audio("hi", {gpt4o.CONF_STREAM_FORMAT: "sse"})
    assert fmt == "mp3"
    assert data == b"data1data2"


@pytest.mark.asyncio
async def test_default_stream_from_entry(monkeypatch):
    entry = DummyEntry(data={"api_key": "k"}, options={gpt4o.CONF_STREAM_FORMAT: "sse"})
    client = GPT4oClient(None, entry)

    lines = [
        b'data: {"type": "speech.audio.delta", "audio": "ZGF0YTE="}\n\n',
        b'data: {"type": "speech.audio.delta", "audio": "ZGF0YTI="}\n\n',
        b'data: {"type": "speech.audio.done"}\n\n',
    ]
    session = DummySSESession(lines)
    monkeypatch.setattr(
        "custom_components.openai_gpt4o_tts.gpt4o.ClientSession",
        lambda timeout=None: session,
    )

    fmt, data = await client.get_tts_audio("hi")
    assert fmt == "mp3"
    assert data == b"data1data2"


@pytest.mark.asyncio
async def test_stream_tts_audio_generator(monkeypatch):
    entry = DummyEntry(data={"api_key": "k"})
    client = GPT4oClient(None, entry)

    lines = [
        b'data: {"type": "speech.audio.delta", "audio": "ZGF0YTE="}\n\n',
        b'data: {"type": "speech.audio.delta", "audio": "ZGF0YTI="}\n\n',
        b'data: {"type": "speech.audio.done"}\n\n',
    ]
    session = DummySSESession(lines)
    monkeypatch.setattr(
        "custom_components.openai_gpt4o_tts.gpt4o.ClientSession",
        lambda timeout=None: session,
    )

    fmt, generator = await client.stream_tts_audio("hi", {gpt4o.CONF_STREAM_FORMAT: "sse"})
    assert fmt == "mp3"
    data = b"".join([chunk async for chunk in generator])
    assert data == b"data1data2"


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
@pytest.mark.parametrize(
    "key",
    [
        "sk-1234567890ABCDEF",
        "sk-proj-ABCDEFG1234567890",
        "sk-svcacct-1234567890ABCDEF",
    ],
)
async def test_log_api_error_masks_api_key_json(caplog, key):
    resp = ErrorResponse(f"invalid key {key}")
    with caplog.at_level("ERROR"):
        await gpt4o._log_api_error(resp)
    assert key not in caplog.text
    assert "sk-***" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key",
    [
        "sk-1234567890ABCDEF",
        "sk-proj-ABCDEFG1234567890",
        "sk-svcacct-1234567890ABCDEF",
    ],
)
async def test_log_api_error_masks_api_key_text(caplog, key):
    resp = ErrorResponse(f"bad request {key}", use_json=False)
    with caplog.at_level("ERROR"):
        await gpt4o._log_api_error(resp)
    assert key not in caplog.text
    assert "sk-***" in caplog.text


def test_volume_gain_clamped_from_entry():
    entry = DummyEntry(
        data={"api_key": "k"}, options={gpt4o.CONF_VOLUME_GAIN: 10.0}
    )
    client = GPT4oClient(None, entry)
    assert client.volume_gain == gpt4o.VOLUME_GAIN_MAX


def test_apply_volume_gain_pcm():
    entry = DummyEntry(data={"api_key": "k"})
    client = GPT4oClient(None, entry)
    pcm = struct.pack("<hh", 1000, -1000)
    boosted = client._apply_volume_gain("pcm", pcm, 2.0)
    assert struct.unpack("<hh", boosted) == (2000, -2000)


def test_resolve_volume_gain_override_clamped():
    entry = DummyEntry(data={"api_key": "k"})
    client = GPT4oClient(None, entry)
    gain = client._resolve_volume_gain({gpt4o.CONF_VOLUME_GAIN: 0.05})
    assert gain == gpt4o.VOLUME_GAIN_MIN
