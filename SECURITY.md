# Security Notes

- **Secrets & API keys**: Store API keys in Home Assistant's secure storage. They are never logged in plaintext; the integration masks tokens before logging (OWASP A3:2021 Sensitive Data Exposure).
- **Transport security**: Only HTTPS endpoints are accepted for Azure. OpenAI requests use HTTPS with bearer/API-key headers to protect data in transit (OWASP A2:2021 Cryptographic Failures).
- **Input validation**: Configuration forms validate audio options, stream formats, and the new volume gain multiplier which is clamped to the 0.1–3.0 safe range to avoid clipping or harmful playback levels (OWASP A4:2021 Insecure Design).
- **Output handling**: Audio scaling operates on in-memory buffers; no shelling out. When optional `pydub` is installed, ensure FFmpeg binaries are trusted and kept patched to avoid introducing vulnerable codecs (OWASP A6:2021 Vulnerable and Outdated Components).
- **Abuse mitigation**: Requests inherit Home Assistant's network timeouts and the integration enforces a 30s API timeout to reduce DoS risk (OWASP A5:2021 Security Misconfiguration).

## Assumptions
- Home Assistant manages API credentials securely and provides rate limiting and authentication for exposed endpoints.
- Users deploying FFmpeg for compressed audio scaling maintain the binary and codecs with security updates.
