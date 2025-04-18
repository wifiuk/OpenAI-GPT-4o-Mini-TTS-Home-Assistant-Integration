"""Constants for OpenAI GPT-4o Mini TTS integration."""

DOMAIN = "openai_gpt4o_tts"
PLATFORMS = ["tts"]

# Configuration keys
CONF_API_KEY = "api_key"
CONF_VOICE = "voice"
CONF_INSTRUCTIONS = "instructions"
CONF_LANGUAGE = "language"

# Default settings
DEFAULT_VOICE = "sage"
DEFAULT_LANGUAGE = "en"

# Default multi-field instruction settings
DEFAULT_AFFECT = (
    "A cheerful guide who delivers speech in a lively and engaging manner, "
    "tailoring pronunciation clearly for the listener."
)
DEFAULT_TONE = (
    "A conversational, friendly tone suitable for general-purpose speech."
)
DEFAULT_PRONUNCIATION = (
    "Use standard pronunciation for the language of the message."
)
DEFAULT_PAUSE = (
    "Insert brief, natural pauses between sentences."
)
DEFAULT_EMOTION = (
    "Subtly expressive; match the content’s sentiment without over‑acting."
)

# Official GPT‑4o TTS voices
OPENAI_TTS_VOICES = [
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "fable",
    "onyx",
    "nova",
    "sage",
    "shimmer",
]

# Full Whisper‑level language support (ISO‑639‑1 codes)
SUPPORTED_LANGUAGES = [
    "af","ar","hy","az","be","bs","bg","ca","zh","hr","cs","da","nl",
    "en","et","fi","fr","gl","de","el","he","hi","hu","is","id","it",
    "ja","kn","kk","ko","lv","lt","mk","ms","mr","mi","ne","no","fa",
    "pl","pt","ro","ru","sr","sk","sl","es","sw","sv","tl","ta","th",
    "tr","uk","ur","vi","cy"
]
