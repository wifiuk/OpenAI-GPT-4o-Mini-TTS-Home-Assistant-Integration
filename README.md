# OpenAI GPT-4o Mini TTS – Home Assistant Integration

**Enhance Home Assistant’s voice assistant with OpenAI’s latest natural-sounding text-to-speech (TTS) model.**  
This integration allows you to use **GPT-4o Mini TTS**, OpenAI’s newest and most expressive TTS model, as a speech provider in Home Assistant.

> **🗣️ Built for [Home Assistant Voice Assistants](https://www.home-assistant.io/voice_control/)**  
> This integration enables GPT-4o Mini TTS in **Assist**.

---

## 🎤 About GPT-4o Mini TTS  

This integration is based on **GPT-4o Mini TTS**, OpenAI’s latest TTS model.  
It offers **high-quality, human-like speech** with **adjustable affect, tone, pronunciation, pauses, and emotion**.

> **OpenAI Quote:**  
> *"Hear and play with these voices in [OpenAI.fm](https://www.OpenAI.fm), our interactive demo for trying the latest text-to-speech model in the OpenAI API. Voices are currently optimized for English."*

With **10 built-in voices**, you can customise **how speech is rendered** to match different scenarios.

---

## 🚀 Features  

✅ **Dual Provider Support**: Works with both **OpenAI** and **Azure AI Foundry**  
✅ **Uses GPT-4o Mini TTS**, OpenAI's latest speech model  
✅ **Fully UI-based setup**—no YAML required  
✅ **10 voices** (`alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`)  
✅ **Customisable speech**—affect, tone, pronunciation, pauses, emotion  
✅ **Works with Home Assistant's Assist**  
✅ **Easily installable via HACS**  
✅ **Playback speed control for faster or slower speech**  
✅ **Streaming audio for quicker responses**  
✅ **Changes take effect immediately – no restart required**  
✅ **Improved error handling and logging**

---

## 🔧 Installation  

### 1️⃣ Install via HACS (Recommended)  

Since this is a **custom repository**, you must add it manually:

1. Open **HACS** in Home Assistant.  
2. Go to **Integrations** → Click the **three-dot menu** → **Custom repositories**.  
3. Add this repository:  
   [https://github.com/wifiuk/OpenAI-GPT-4o-Mini-TTS-Home-Assistant-Integration.git](https://github.com/wifiuk/OpenAI-GPT-4o-Mini-TTS-Home-Assistant-Integration.git)
4. Select **Integration** as the category and click **Add**.  
5. Click **Download** and install **OpenAI GPT-4o Mini TTS**.  
6. **Restart Home Assistant** after installation.  

---

### 2️⃣ Manual Installation (Alternative)  

1. Download this repository as a **ZIP file** and extract it.  
2. Copy the `openai_gpt4o_tts` folder to:  /config/custom_components/  
3. Restart Home Assistant.  
4. Go to **Settings → Devices & Services → Add Integration**.  
5. Search for **OpenAI GPT-4o Mini TTS** and follow the setup process.  

---

## 🛠️ Setup & Configuration  

### Provider Selection

During setup, you can choose between two providers:
- **OpenAI**: Use OpenAI's public API
- **Azure AI Foundry**: Use Azure's OpenAI service

### OpenAI Setup

1. **Go to:** Settings → Devices & Services → Integrations.  
2. **Click "+ Add Integration"** → Select **OpenAI GPT-4o Mini TTS**.  
3. **Select Provider:** Choose **OpenAI**  
4. **Enter your OpenAI API Key.**  
5. **Choose a Voice** from the dropdown (e.g., `nova`, `onyx`, `sage`).

### Azure AI Foundry Setup

1. **Go to:** Settings → Devices & Services → Integrations.  
2. **Click "+ Add Integration"** → Select **OpenAI GPT-4o Mini TTS**.  
3. **Select Provider:** Choose **Azure AI Foundry**  
4. **Enter your Azure API Key.**  
5. **Enter your Azure Endpoint URL** (example format below)  
6. **Choose a Voice** from the dropdown (e.g., `nova`, `onyx`, `sage`).

**Azure Endpoint Format:**
```
https://{resource-name}.cognitiveservices.azure.com/openai/deployments/{deployment-name}/audio/speech?api-version=2025-03-01-preview
```

### Common Configuration Steps

4. **Choose a Voice** from the dropdown (e.g., `nova`, `onyx`, `sage`).
5. **Customize the speech settings:**
- **Affect/Personality** (e.g., "A cheerful guide")  
- **Tone** (e.g., "Friendly, clear, and reassuring")  
- **Pronunciation** (e.g., "Clear, articulate, and steady")  
- **Pauses** (e.g., "Brief, purposeful pauses after key instructions")
- **Emotion** (e.g., "Warm and supportive")
- **Playback Speed** (e.g., `1.2` for 20% faster)
- **Volume Gain** (0.1–3.0, default `1.0`) boosts or reduces loudness without clipping
- **Model** (e.g., `gpt-4o-mini-tts`)
- **Audio Format** (e.g., `mp3`, `wav`)
- **Stream Format** – choose `sse` to stream audio while it is generated or `audio` to wait for the full file
6. Click **Submit**. 🎉 Done!


<img width="334" height="1045" alt="image" src="https://github.com/user-attachments/assets/fb6f147e-b016-4766-bcb9-f1ddeec87ffa" />


Now, Home Assistant's voice assistant will use GPT-4o Mini TTS as its **speech provider**.

---

## 🔊 Using GPT-4o TTS in Home Assistant  

### 🔹 **Enable GPT-4o Mini TTS in Home Assistant Voice Assistants**  

Once the repo is installed, follow these steps:  

1. **Go to:** `Settings → Voice Assistants`.  
2. **Choose your assistant** (e.g., Assist).  
3. Scroll down to **Text-to-Speech** settings.  
4. **Select "OpenAI GPT-4o Mini TTS" from the dropdown**.  
5. **Choose the same voice you set up earlier**    
6. **Save settings** and test voice output.

![image](https://github.com/user-attachments/assets/6f61f299-1c51-4109-ab5b-f7b1a1e6f658)

👉 **See Home Assistant’s [Voice Control Guide](https://www.home-assistant.io/voice_control/) for setup.**  

---

## 📝 FAQ  

### **How do I get an OpenAI API Key?**  
You need an API key from OpenAI to use this integration. Get one from:  
👉 [https://platform.openai.com/signup/](https://platform.openai.com/signup/)  

### **What are the available voices?**
The integration supports the following **10 voices**:  alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer


### **Can I make the audio louder or softer?**
Yes. Set **Volume Gain** between **0.1** and **3.0** in the integration options or per service call. Values outside that range are clamped to prevent ear-damaging spikes or digital clipping. For compressed formats (MP3/AAC/Opus), install [`pydub`](https://github.com/jiaaro/pydub) and FFmpeg so the integration can adjust gain safely; WAV/PCM files are handled natively.


### **Is this free to use?**  
No, **OpenAI's API is a paid service**. You are charged per character generated. Check OpenAI's pricing page for more details.  

### **How do I get an Azure API Key and Endpoint?**  
To use Azure AI Foundry:
1. Sign up for an Azure account at [https://azure.microsoft.com](https://azure.microsoft.com)
2. Create an Azure OpenAI resource in Azure Portal
3. Deploy the `gpt-4o-mini-tts` model in your resource
4. Get your API key from the "Keys and Endpoint" section
5. Construct your endpoint URL using the format shown in the Azure setup section above

### **What's the difference between OpenAI and Azure providers?**  
Both providers use the same GPT-4o Mini TTS model and support the same features (voices, settings, streaming). The main differences are:
- **OpenAI**: Direct access to OpenAI's public API, simpler setup
- **Azure**: Enterprise-grade security, compliance, and integration with Azure services

---

## 🔄 Recent Updates

**Dual Provider Support** - Added support for Azure AI Foundry alongside OpenAI
Streaming mode enabled for immediate playback

### Developer Notes

- **Run tests:** `pytest`
- **Optional deps for audio scaling:** `pip install pydub` and ensure FFmpeg is on your PATH for compressed audio gain control.

---

## 🤝 Contributing  

Want to help improve this project? Contributions are welcome!  

1. Fork the repo  
2. Submit pull requests for features/fixes  
3. Report issues or suggest improvements  

---

## 📢 Support  

Have questions or need help?  
- **GitHub Issues:** Report problems [here](https://github.com/wifiuk/OpenAI-GPT-4o-Mini-TTS-Home-Assistant-Integration/issues)  
- **Home Assistant Forums:** Share feedback [here](https://community.home-assistant.io)  

Enjoy **human-like, expressive TTS** in Home Assistant! 🎤🔊
