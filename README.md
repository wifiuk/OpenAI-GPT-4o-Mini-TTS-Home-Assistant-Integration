# OpenAI GPT-4o Mini TTS (v1.0.9)

## Overview
Home Assistant custom integration that exposes OpenAI's GPT-4o Mini text-to-speech API as a TTS provider. The codebase matches the upstream 1.0.9 release published on 23 July 2024 and removes later experimental features that regressed streaming stability.

## Prerequisites
- Home Assistant 2024.6 or newer with HACS available.
- OpenAI API key (`sk-...`) with access to the audio endpoint.
- FFmpeg installed on the Home Assistant host (required by the core TTS pipeline).

## Installation
1. **HACS (recommended)**
   - In HACS → Integrations → three-dot menu → *Custom repositories*, add `https://github.com/wifiuk/OpenAI-GPT-4o-Mini-TTS-Home-Assistant-Integration` as category **Integration**.
   - Install **OpenAI GPT-4o Mini TTS** and restart Home Assistant.
2. **Manual**
   - Copy `custom_components/openai_gpt4o_tts` into `<config>/custom_components/`.
   - Ensure `manifest.json` reports version `1.0.9`.
   - Restart Home Assistant.

## Configuration
1. Navigate to **Settings → Devices & Services → + Add Integration**.
2. Select **OpenAI GPT-4o Mini TTS**.
3. Provide the OpenAI API key when prompted.
4. Optional tweaks (validated by the UI schema):
   - Voice: one of `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`.
   - Playback speed between `0.25` and `4.0`.
   - Audio output format (default `mp3`) and stream format (`audio` for full responses, `sse` for chunked streaming).
   - Multi-field instructions (affect, tone, pronunciation, pause, emotion) that are combined into the `instructions` payload.
5. Assign the created TTS entity to any Assist or Voice Assistant pipeline as needed.

## Usage & Testing
- Use the **Test** button under **Settings → Devices & Services → OpenAI GPT-4o Mini TTS** to confirm playback.
- Developer Tools → Services: call `tts.openai_gpt4o_tts_say` with overrides such as `{ "voice": "nova", "audio_output": "wav" }`.
- Local testing: `pytest` (requires Home Assistant stubs; optional dependencies are not bundled).

## Security Notes
- API keys are stored by Home Assistant; the integration only logs masked values.
- Outbound calls target `https://api.openai.com/v1/audio/speech` with a 30s client timeout.
- No secrets or configuration values are committed to the repository; runtime secrets must be injected via Home Assistant.

## Limitations
- The integration depends on OpenAI uptime and does not cache generated audio.
- SSE streaming is only available when the OpenAI API returns chunked responses; otherwise playback waits for the full file.
