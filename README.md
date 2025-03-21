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

With **11 built-in voices**, you can customise **how speech is rendered** to match different scenarios.

---

## 🚀 Features  

✅ **Uses GPT-4o Mini TTS**, OpenAI’s latest speech model  
✅ **Fully UI-based setup**—no YAML required  
✅ **11 voices** (`alloy`, `ash`, `ballad`, `coral`, `echo`, etc.)  
✅ **Customisable speech**—affect, tone, pronunciation, pauses, emotion  
✅ **Works with Home Assistant’s Assist, Piper, and Whisper**  
✅ **Easily installable via HACS**  

---

## 🔧 Installation  

### 1️⃣ Install via HACS (Recommended)  

Since this is a **custom repository**, you must add it manually:

1. Open **HACS** in Home Assistant.  
2. Go to **Integrations** → Click the **three-dot menu** → **Custom repositories**.  
3. Add this repository:  [https://github.com/wifiuk/OpenAI-GPT-4o-Mini-TTS-Home-Assistant-Integration.git](https://github.com/wifiuk/OpenAI-GPT-4o-Mini-TTS-Home-Assistant-Integration.git)


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

1. **Go to:** Settings → Devices & Services → Integrations.  
2. **Click “+ Add Integration”** → Select **OpenAI GPT-4o Mini TTS**.  
3. **Enter your OpenAI API Key.**  
4. **Choose a Voice** from the dropdown (e.g., `nova`, `onyx`, `sage`).  
5. **Customise the speech settings:**  
- **Affect/Personality** (e.g., "A cheerful guide")  
- **Tone** (e.g., "Friendly, clear, and reassuring")  
- **Pronunciation** (e.g., "Clear, articulate, and steady")  
- **Pauses** (e.g., "Brief, purposeful pauses after key instructions")  
- **Emotion** (e.g., "Warm and supportive")  
6. Click **Submit**. 🎉 Done!  

Now, Home Assistant's voice assistant will use GPT-4o Mini TTS as its **speech provider**.

---

## 🔊 Using GPT-4o TTS in Home Assistant  

### 🔹 **Voice Assistants (Main Use Case)**  

This TTS engine is built for **Home Assistant’s voice assistant platform**. You can configure it as a **speech provider** in:  

- **Assist (HA’s built-in assistant)**  

👉 **See Home Assistant’s [Voice Control Guide](https://www.home-assistant.io/voice_control/) for setup.**  

---

## 📝 FAQ  

### **How do I get an OpenAI API Key?**  
You need an API key from OpenAI to use this integration. Get one from:  
👉 [https://platform.openai.com/signup/](https://platform.openai.com/signup/)  

### **What are the available voices?**  
The integration supports the following **11 voices**:  


