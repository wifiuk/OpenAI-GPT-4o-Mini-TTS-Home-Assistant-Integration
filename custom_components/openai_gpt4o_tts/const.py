"""Constants for OpenAI GPT-4o Mini TTS integration."""

DOMAIN = "openai_gpt4o_tts"
PLATFORMS = ["tts"]

# Configuration keys
CONF_API_KEY = "api_key"
CONF_VOICE = "voice"
CONF_INSTRUCTIONS = "instructions"

# Default voice setting
DEFAULT_VOICE = "sage"

# Default multi-field instruction settings
DEFAULT_AFFECT = (
    "A cheerful guide who delivers speech in a lively and engaging manner, "
    "keeping the listener's attention while providing clear guidance."
)
DEFAULT_TONE = (
    "Friendly, clear, and reassuring, creating a calm atmosphere and making the listener "
    "feel confident and comfortable. Encourages attentiveness without being overly formal."
)
DEFAULT_PRONUNCIATION = (
    "Clear, articulate, and steady, ensuring each instruction is easily understood "
    "while maintaining a natural, conversational flow. Uses proper enunciation "
    "to minimize misunderstandings."
)
DEFAULT_PAUSE = (
    "Brief, purposeful pauses after key instructions (e.g., 'cross the street' and 'turn right') "
    "to allow time for the listener to process the information and follow along. "
    "Ensures clarity without unnecessary delays."
)
DEFAULT_EMOTION = (
    "Warm and supportive, conveying empathy and care, ensuring the listener feels guided "
    "and safe throughout the journey. Uses subtle emotional cues to enhance engagement."
)

# Official GPT-4o TTS voices
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
    "shimmer"
]
