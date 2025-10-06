# Security Notes

- **OWASP A02:2021 – Cryptographic Failures**: Secrets (OpenAI API keys) are stored by Home Assistant and only referenced via the config entry. Keys are masked before logging using `_mask_api_keys`.
- **OWASP A05:2021 – Security Misconfiguration**: All outbound requests enforce HTTPS, a 30s timeout, and never shell out to the host. The integration offers no YAML templating or dynamic code execution.
- **OWASP A10:2021 – Server-Side Request Forgery**: The integration sends traffic exclusively to `https://api.openai.com/v1/audio/speech`; no user-provided URLs are accepted.
- **Input validation**: Config schemas allow-list voice, model, audio, and stream formats and coerce playback speed into `0.25–4.0`. Instructions fields are length-limited (5–500 chars).
- **Output handling**: SSE streams and base64 payloads are decoded with error handling, and unexpected data is ignored with a warning to avoid poisoning downstream FFmpeg pipelines.

## Assumptions & Risks
- Home Assistant provides authentication, rate limiting, and protects `tts_proxy` endpoints from anonymous access.
- Operators rotate API keys and enforce least privilege on their OpenAI accounts.
- Network interruptions return empty audio and log sanitized errors; no retry or caching is implemented.
