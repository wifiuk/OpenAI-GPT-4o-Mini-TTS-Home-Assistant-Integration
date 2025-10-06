"""Client for OpenAI GPT-4o Mini TTS."""

import asyncio
import audioop
import base64
import binascii
import contextlib
import io
import json
import logging
import math
import re
import wave
from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout
from typing import Optional

from .const import (
    CONF_PROVIDER,
    CONF_AZURE_ENDPOINT,
    CONF_INSTRUCTIONS,
    CONF_PLAYBACK_SPEED,
    CONF_VOICE,
    CONF_MODEL,
    CONF_AUDIO_OUTPUT,
    CONF_STREAM_FORMAT,
    PROVIDER_OPENAI,
    PROVIDER_AZURE,
    DEFAULT_PROVIDER,
    DEFAULT_PLAYBACK_SPEED,
    DEFAULT_VOICE,
    DEFAULT_MODEL,
    DEFAULT_AUDIO_OUTPUT,
    DEFAULT_STREAM_FORMAT,
    CONF_VOLUME_GAIN,
    DEFAULT_VOLUME_GAIN,
    VOLUME_GAIN_MIN,
    VOLUME_GAIN_MAX,
)

_LOGGER = logging.getLogger(__name__)

# Request timeout for the OpenAI API in seconds
REQUEST_TIMEOUT = 30

# API endpoint for speech generation
OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"

# Regex to detect API keys so they can be masked in logs. Keys may include
# prefixes like ``sk-proj-`` or ``sk-svcacct-`` so we allow hyphens in the
# character set and require a reasonable length to avoid false positives.
_API_KEY_RE = re.compile(r"sk-[A-Za-z0-9-]{16,}")

# Allow-list of characters that appear in base64 payloads so we can
# differentiate real binary audio (which often contains NULL bytes) from a
# JSON/base64 encoded string. This guards against feeding ffmpeg invalid data
# (OWASP A5:2021 – Security Misconfiguration).
_BASE64_BYTES_RE = re.compile(rb"^[A-Za-z0-9+/=\r\n]+$")

# Maximum amount of buffered SSE text we will accumulate before resetting to
# avoid unbounded growth if the provider misbehaves (OWASP A7:2021 –
# Identification and Authentication Failures -> resource exhaustion).
_MAX_SSE_BUFFER_BYTES = 1_000_000

try:  # pragma: no cover - optional dependency
    from pydub import AudioSegment
except ImportError:  # pragma: no cover - optional dependency
    AudioSegment = None


def _mask_api_keys(text: str) -> str:
    """Return ``text`` with API keys masked."""
    return _API_KEY_RE.sub("sk-***", text)


def _maybe_decode_base64_bytes(data: bytes) -> Optional[bytes]:
    """Return decoded bytes when ``data`` looks like base64, else ``None``."""

    if not data:
        return None

    sample = data.strip()
    if not sample or len(sample) < 8:  # too small to be meaningful audio
        return None

    if not _BASE64_BYTES_RE.fullmatch(sample):
        return None

    try:
        decoded = base64.b64decode(sample, validate=True)
    except (binascii.Error, ValueError):
        return None

    # Guard against decoding plain ASCII speech which would expand in size.
    if not decoded or len(decoded) >= len(sample):
        return None

    return decoded


async def _log_api_error(resp: ClientResponse) -> None:
    """Log error details returned by the OpenAI API."""
    try:
        data = await resp.json()
        message = data.get("error", {}).get("message", str(data))
    except Exception:  # pragma: no cover - non-JSON error
        message = await resp.text()
    sanitized = _mask_api_keys(str(message))
    _LOGGER.error("OpenAI TTS API error %s: %s", resp.status, sanitized)


class GPT4oClient:
    """Handles direct calls to OpenAI's /v1/audio/speech for GPT-4o TTS."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        # Get provider and API key
        self._provider = entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
        self._api_key = entry.data["api_key"]
        self._azure_endpoint = entry.data.get(CONF_AZURE_ENDPOINT, "")

        # Pull default voice/instructions from options first, then legacy data
        opts = getattr(entry, "options", {}) or {}
        self._voice = opts.get(CONF_VOICE, entry.data.get(CONF_VOICE))
        self._instructions = opts.get(
            CONF_INSTRUCTIONS, entry.data.get(CONF_INSTRUCTIONS)
        )
        self._playback_speed = float(
            opts.get(
                CONF_PLAYBACK_SPEED,
                entry.data.get(CONF_PLAYBACK_SPEED, DEFAULT_PLAYBACK_SPEED),
            )
        )
        self._model = opts.get(
            CONF_MODEL, entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        )
        self._audio_output = opts.get(
            CONF_AUDIO_OUTPUT, entry.data.get(CONF_AUDIO_OUTPUT, DEFAULT_AUDIO_OUTPUT)
        )
        self._stream_format = opts.get(
            CONF_STREAM_FORMAT, entry.data.get(CONF_STREAM_FORMAT, DEFAULT_STREAM_FORMAT)
        )
        raw_gain = opts.get(
            CONF_VOLUME_GAIN, entry.data.get(CONF_VOLUME_GAIN, DEFAULT_VOLUME_GAIN)
        )
        self._volume_gain = self._sanitize_volume_gain(raw_gain, log_on_change=False)

    def _get_endpoint(self) -> str:
        """Return the appropriate API endpoint based on provider."""
        if self._provider == PROVIDER_AZURE:
            return self._azure_endpoint
        return OPENAI_TTS_ENDPOINT

    def _get_headers(self) -> dict:
        """Return the appropriate headers based on provider."""
        if self._provider == PROVIDER_AZURE:
            return {
                "api-key": self._api_key,
                "Content-Type": "application/json",
            }
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @property
    def stream_format(self) -> str:
        """Return the default stream format."""
        return self._stream_format

    async def _iter_sse_audio(self, resp: ClientResponse):
        """Yield audio bytes from an SSE response with robust framing."""

        def _flush_event(payload: str) -> Optional[dict]:
            data = payload.strip()
            if not data:
                return None
            if data == "[DONE]":
                return {"type": "speech.audio.done"}
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                sanitized = _mask_api_keys(data[:128])
                _LOGGER.debug("Discarding invalid SSE payload prefix: %s", sanitized)
                return None

        buffer = ""
        data_lines: list[str] = []

        async for raw in resp.content.iter_chunked(1024):
            if not raw:
                continue
            try:
                chunk = raw.decode("utf-8")
            except UnicodeDecodeError:
                _LOGGER.warning("Non UTF-8 data in SSE stream; dropping chunk")
                continue

            buffer += chunk
            if len(buffer) > _MAX_SSE_BUFFER_BYTES:
                _LOGGER.warning(
                    "SSE buffer exceeded %s bytes; resetting to avoid exhaustion",
                    _MAX_SSE_BUFFER_BYTES,
                )
                buffer = ""
                data_lines.clear()
                continue

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.rstrip("\r")

                if not line:
                    if not data_lines:
                        continue
                    event = _flush_event("\n".join(data_lines))
                    data_lines.clear()
                    if not event:
                        continue
                    event_type = event.get("type")
                    if event_type == "speech.audio.delta":
                        audio_b64 = event.get("audio", "")
                        if isinstance(audio_b64, str) and audio_b64:
                            try:
                                yield base64.b64decode(audio_b64, validate=True)
                            except (binascii.Error, ValueError):
                                _LOGGER.warning("Invalid audio chunk in SSE stream")
                    if event_type == "speech.audio.done":
                        return
                    continue

                if line.startswith(":"):
                    continue  # comment/heartbeat per SSE spec

                if line.startswith("data:"):
                    data_line = line[5:]
                    if data_line.startswith(" "):
                        data_line = data_line[1:]
                    data_lines.append(data_line)
                    continue

                # Ignore other SSE fields we do not rely on for now

        if data_lines:
            event = _flush_event("\n".join(data_lines))
            if not event:
                return
            if event.get("type") == "speech.audio.delta":
                audio_b64 = event.get("audio", "")
                if isinstance(audio_b64, str) and audio_b64:
                    try:
                        yield base64.b64decode(audio_b64, validate=True)
                    except (binascii.Error, ValueError):
                        _LOGGER.warning("Invalid audio chunk in trailing SSE payload")
            if event.get("type") == "speech.audio.done":
                return

    @property
    def audio_output(self) -> str:
        """Return the default audio output format."""
        return self._audio_output

    @property
    def volume_gain(self) -> float:
        """Return the configured default volume gain multiplier."""
        return self._volume_gain

    def _sanitize_volume_gain(self, value: Optional[float], *, log_on_change: bool = True) -> float:
        """Normalize a user-provided gain into the supported safe range."""
        try:
            gain = float(value)
        except (TypeError, ValueError):
            if log_on_change:
                _LOGGER.warning(
                    "Invalid volume gain %s; using %.2f", value, DEFAULT_VOLUME_GAIN
                )
            return DEFAULT_VOLUME_GAIN

        if not math.isfinite(gain):
            if log_on_change:
                _LOGGER.warning(
                    "Non-finite volume gain %s; using %.2f", value, DEFAULT_VOLUME_GAIN
                )
            return DEFAULT_VOLUME_GAIN

        clamped = max(VOLUME_GAIN_MIN, min(gain, VOLUME_GAIN_MAX))
        if log_on_change and not math.isclose(clamped, gain, rel_tol=1e-3, abs_tol=1e-3):
            _LOGGER.warning(
                "Volume gain %.2f adjusted into safe range %.1f–%.1f", gain, VOLUME_GAIN_MIN, VOLUME_GAIN_MAX
            )
        return clamped

    def _resolve_volume_gain(self, options: Optional[dict]) -> float:
        """Return gain override if provided, otherwise default."""
        if options and CONF_VOLUME_GAIN in options:
            return self._sanitize_volume_gain(options.get(CONF_VOLUME_GAIN))
        return self._volume_gain

    def _scale_pcm_frames(self, frames: bytes, sample_width: int, gain: float) -> Optional[bytes]:
        """Apply gain to PCM frames with saturation handling."""
        if sample_width not in (1, 2, 3, 4):
            _LOGGER.warning("Unsupported PCM sample width %s; skipping gain", sample_width)
            return None
        try:
            return audioop.mul(frames, sample_width, gain)
        except Exception as err:  # pragma: no cover - defensive
            _LOGGER.warning("Failed to scale PCM audio safely: %s", err)
            return None

    def _apply_volume_gain(self, audio_format: str, audio_bytes: bytes, gain: float) -> bytes:
        """Scale audio bytes according to ``gain`` while respecting safe bounds."""
        if not audio_bytes:
            return audio_bytes

        safe_gain = self._sanitize_volume_gain(gain)
        if math.isclose(safe_gain, 1.0, rel_tol=1e-3, abs_tol=1e-3):
            return audio_bytes

        fmt = (audio_format or "").lower()

        if fmt in {"wav", "wave"}:
            try:
                with contextlib.closing(wave.open(io.BytesIO(audio_bytes), "rb")) as wav_in:
                    params = wav_in.getparams()
                    frames = wav_in.readframes(params.nframes)
            except (wave.Error, EOFError, OSError) as err:
                _LOGGER.warning("Unable to read WAV audio for gain adjustment: %s", err)
                return audio_bytes
            scaled = self._scale_pcm_frames(frames, params.sampwidth, safe_gain)
            if scaled is None:
                return audio_bytes
            out_buf = io.BytesIO()
            with contextlib.closing(wave.open(out_buf, "wb")) as wav_out:
                wav_out.setparams(params)
                wav_out.writeframes(scaled)
            return out_buf.getvalue()

        if fmt == "pcm":
            scaled = self._scale_pcm_frames(audio_bytes, 2, safe_gain)
            if scaled is None:
                _LOGGER.warning(
                    "PCM gain adjustment skipped; ensure 16-bit PCM when requesting scaling"
                )
                return audio_bytes
            return scaled

        if AudioSegment is not None and fmt:
            try:
                segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
                delta_db = 20 * math.log10(safe_gain)
                boosted = segment.apply_gain(delta_db)
                export_buf = io.BytesIO()
                boosted.export(export_buf, format=fmt)
                return export_buf.getvalue()
            except Exception as err:  # pragma: no cover - codec/ffmpeg issues
                _LOGGER.warning(
                    "Unable to apply volume gain to %s audio: %s", fmt, err
                )
                return audio_bytes

        if fmt not in {"", "wav", "wave", "pcm"} and AudioSegment is None:
            _LOGGER.warning(
                "Install pydub and FFmpeg to enable safe volume scaling for %s audio", fmt
            )

        return audio_bytes

    def _extract_audio_bytes(self, audio_format: str, audio_bytes: bytes) -> bytes:
        """Return binary audio, decoding base64/JSON payloads when necessary."""

        if not audio_bytes:
            return audio_bytes

        fmt = (audio_format or "").lower()

        # Some providers wrap PCM data in base64; decode it safely before
        # handing to Home Assistant to avoid ffmpeg failures downstream.
        if fmt == "pcm":
            decoded = _maybe_decode_base64_bytes(audio_bytes)
            if decoded is not None:
                return decoded

        # Defensive: occasionally Azure responses may contain JSON with a
        # base64 encoded payload. Detect and decode so we only ever return
        # binary audio.
        try:
            text_payload = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return audio_bytes

        try:
            parsed = json.loads(text_payload)
        except json.JSONDecodeError:
            return audio_bytes

        if isinstance(parsed, dict):
            for key in ("audio", "data", "value"):
                candidate = parsed.get(key)
                if isinstance(candidate, str):
                    decoded = _maybe_decode_base64_bytes(candidate.encode("utf-8"))
                    if decoded is not None:
                        return decoded

        return audio_bytes

    async def iter_tts_audio(self, text: str, options: dict | None = None):
        """Asynchronously yield audio chunks from the API."""
        if options is None:
            options = {}

        voice = options.get("voice", self._voice) or DEFAULT_VOICE
        instructions = options.get("instructions", self._instructions) or ""
        audio_format = options.get("audio_output", self._audio_output)
        model = options.get(CONF_MODEL, self._model)
        stream_format = options.get(CONF_STREAM_FORMAT, self._stream_format)

        headers = self._get_headers()
        endpoint = self._get_endpoint()
        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "instructions": instructions,
            "response_format": audio_format,
            "speed": float(options.get(CONF_PLAYBACK_SPEED, self._playback_speed)),
            "stream_format": stream_format,
        }

        timeout = ClientTimeout(total=REQUEST_TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            async with session.post(
                endpoint,
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status >= 400:
                    await _log_api_error(resp)
                    return
                if stream_format == "sse":
                    async for chunk in self._iter_sse_audio(resp):
                        yield chunk
                else:
                    async for chunk in resp.content.iter_chunked(8192):
                        if chunk:
                            yield chunk

    async def get_tts_audio(self, text: str, options: dict | None = None):
        """Generate TTS audio from GPT-4o using direct HTTP calls."""
        if options is None:
            options = {}

        try:
            audio_chunks = [chunk async for chunk in self.iter_tts_audio(text, options)]
            if not audio_chunks:
                return None, None
            audio_format = options.get("audio_output", self._audio_output)
            gain = self._resolve_volume_gain(options)
            joined = b"".join(audio_chunks)
            audio_bytes = self._extract_audio_bytes(audio_format, joined)
            return audio_format, self._apply_volume_gain(audio_format, audio_bytes, gain)
        except asyncio.TimeoutError:
            _LOGGER.error(
                "GPT-4o TTS request timed out after %s seconds", REQUEST_TIMEOUT
            )
        except ClientError as err:
            _LOGGER.error("Error generating GPT-4o TTS audio: %s", err)
        except Exception as err:  # pragma: no cover - unexpected errors
            _LOGGER.error("Unexpected error generating GPT-4o TTS audio: %s", err)
        return None, None

    async def stream_tts_audio(self, text: str, options: dict | None = None):
        """Return async iterator for TTS audio without joining chunks."""
        if options is None:
            options = {}
        audio_format = options.get("audio_output", self._audio_output)
        try:
            return audio_format, self.iter_tts_audio(text, options)
        except Exception as err:  # pragma: no cover - unexpected errors
            _LOGGER.error("Error starting GPT-4o TTS stream: %s", err)
            return None, None
