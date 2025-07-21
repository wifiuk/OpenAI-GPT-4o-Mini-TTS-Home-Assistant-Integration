import asyncio
from aiohttp import web
import importlib.util
import pathlib
import types
import sys
import pytest

MODULE_PATH = (
    pathlib.Path(__file__).parents[1] / "custom_components/openai_gpt4o_tts/gpt4o.py"
)
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
spec = importlib.util.spec_from_file_location(
    "custom_components.openai_gpt4o_tts.gpt4o", MODULE_PATH
)
gpt4o = importlib.util.module_from_spec(spec)
sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
pkg = types.ModuleType("custom_components.openai_gpt4o_tts")
sys.modules.setdefault("custom_components.openai_gpt4o_tts", pkg)
setattr(sys.modules["custom_components"], "openai_gpt4o_tts", pkg)
const_path = (
    pathlib.Path(__file__).parents[1] / "custom_components/openai_gpt4o_tts/const.py"
)
spec_const = importlib.util.spec_from_file_location(
    "custom_components.openai_gpt4o_tts.const",
    const_path,
)
const = importlib.util.module_from_spec(spec_const)
spec_const.loader.exec_module(const)
sys.modules["custom_components.openai_gpt4o_tts.const"] = const
setattr(pkg, "const", const)
spec.loader.exec_module(gpt4o)
GPT4oClient = gpt4o.GPT4oClient
API_URL = gpt4o.API_URL
sys.modules["custom_components.openai_gpt4o_tts.gpt4o"] = gpt4o
setattr(pkg, "gpt4o", gpt4o)
from custom_components.openai_gpt4o_tts.const import CONF_VOICE, CONF_INSTRUCTIONS


class FakeHass:
    async def async_add_executor_job(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)


class FakeEntry:
    data = {"api_key": "test"}
    options = {CONF_VOICE: "nova", CONF_INSTRUCTIONS: "test"}


async def _start_server(chunks):
    async def handler(request):
        await request.json()
        resp = web.StreamResponse(status=200)
        await resp.prepare(request)
        for chunk in chunks:
            await resp.write(chunk)
        return resp

    app = web.Application()
    app.router.add_post("/v1/audio/speech", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    return runner, f"http://localhost:{port}/v1/audio/speech"


@pytest.mark.asyncio
async def test_iter_tts_audio(monkeypatch):
    chunks = [b"a", b"b", b"c"]
    runner, url = await _start_server(chunks)
    monkeypatch.setattr("custom_components.openai_gpt4o_tts.gpt4o.API_URL", url)
    client = GPT4oClient(FakeHass(), FakeEntry())

    received = []
    async for chunk in client.iter_tts_audio("hello"):
        received.append(chunk)
    assert b"".join(received) == b"".join(chunks)
    await runner.cleanup()
