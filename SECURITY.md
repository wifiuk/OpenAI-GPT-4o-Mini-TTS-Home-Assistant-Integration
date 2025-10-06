# Security Notes

- **Secrets**: API keys are stored by Home Assistant's secret storage. The integration masks tokens in logs to limit exposure (OWASP A3:2021 Sensitive Data Exposure).
- **Transport**: Only HTTPS endpoints are accepted. Client requests enforce a 30s timeout and never shell out, reducing injection and SSRF risk (OWASP A5:2021 Security Misconfiguration, A10:2021 Server-Side Request Forgery).
- **Input validation**: Configuration schemas restrict provider, voice, model, audio format, playback speed, and volume gain. Gain is clamped to `0.1–3.0` at runtime to avoid clipping or harmful playback (OWASP A4:2021 Insecure Design).
- **Output handling**: Audio returned from providers is normalised to binary and sanitized before being passed to ffmpeg, preventing malformed base64 payloads from propagating downstream (OWASP A1:2021 Broken Access Control via injection vectors).
- **Dependencies**: Optional FFmpeg/pydub components must be maintained by the operator to avoid vulnerable codecs (OWASP A6:2021 Vulnerable and Outdated Components).

## Assumptions & Risks
- Home Assistant provides authentication, rate limiting, and protects the `/api/tts_proxy` endpoint from abuse.
- API credentials are provisioned with the minimum scope required and rotated by the operator.
- Outbound connectivity to OpenAI/Azure is available; transient failures result in log warnings and no cached audio.
