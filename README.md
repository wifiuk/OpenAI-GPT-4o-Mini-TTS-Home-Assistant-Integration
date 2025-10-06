# OpenAI GPT-4o Mini TTS Home Assistant Integration

## Overview
Use GPT-4o Mini TTS or the Azure equivalent as a Text-to-Speech provider inside Home Assistant. The integration is compatible with Assist and any feature that consumes Home Assistant's TTS entities.

## Prerequisites
- Home Assistant 2024.6 or newer with HACS installed.
- OpenAI API key (`sk-...`) **or** Azure OpenAI deployment with endpoint URL and API key.
- Optional for volume gain on compressed formats: `pydub` + FFmpeg available on the host.

## Installation
1. **HACS (recommended)**
   - In HACS → Integrations → three-dot menu → Custom repositories, add `https://github.com/wifiuk/OpenAI-GPT-4o-Mini-TTS-Home-Assistant-Integration` as an Integration.
   - Install **OpenAI GPT-4o Mini TTS** and restart Home Assistant.
2. **Manual**
   - Copy `custom_components/openai_gpt4o_tts` to `<config>/custom_components/`.
   - Restart Home Assistant.

## Configuration
1. In Home Assistant → Settings → Devices & Services → *Add Integration* → **OpenAI GPT-4o Mini TTS**.
2. Select provider (**OpenAI** or **Azure AI Foundry**).
3. Provide the API key and, for Azure, the HTTPS endpoint.
4. Optional tuning (validated in UI):
   - Voice (`alloy`, `nova`, ...), playback speed `0.25–4.0`, volume gain `0.1–3.0`.
   - Audio output (`mp3`, `wav`, `opus`, `aac`, `flac`, `pcm`). PCM payloads are decoded before delivery to keep ffmpeg happy.
   - Stream format (`audio` or `sse`).
   - Free-form instructions assembled from affect, tone, pronunciation, pause, emotion fields.
5. Assign the entity as the Text-to-Speech engine in Settings → Voice Assistants.

## Usage
Invoke `tts.openai_gpt4o_tts_say` or use Assist; options in service calls override defaults. Volume gain is range-checked and sanitised before applying.

## Development
```bash
pip install -r tests/requirements.txt  # if provided by your setup
pytest
```

## Security Notes
- API keys are stored by Home Assistant and masked in logs.
- All outbound calls enforce HTTPS endpoints, 30s client timeout, and no shell commands are executed.
- PCM responses are decoded from base64 before streaming to avoid feeding invalid data into ffmpeg pipelines.
- Streaming responses validate UTF-8 SSE chunks and bound buffering to 1 MB to avoid connection resets and resource exhaustion.

## Limitations
- Network access to OpenAI/Azure is required; the integration does not cache audio.
- Streaming relies on the provider delivering SSE events; fallback joins the full audio payload when SSE is disabled.
