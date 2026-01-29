# 🎙️ Neha – Real-Time Voice AI Telecaller (Outbound Sales Agent)

Neha is a **real-time, low-latency Voice AI outbound telecalling system** designed for **bulk food catering sales** at **Hogest Technologies, Chennai**.  
It listens, thinks, and speaks like a real human telecaller with **barge-in support**, **live speech-to-text**, **AI-driven conversation flow**, and **natural Indian voice output**.

This project is built for **production-grade outbound calling**, not demos.

---

## 🚀 Key Capabilities

- 🎧 **Real-time speech recognition** (Deepgram Flux v2)
- 🧠 **Context-aware AI conversation engine** (OpenAI GPT)
- 🔊 **Natural Indian voice TTS** (ElevenLabs)
- ✋ **Barge-in support** (interrupt AI while user speaks)
- ⚡ **Low-latency audio streaming** (20ms frames)
- 📞 **Outbound sales conversation logic** (telecaller-style)
- 🧩 **Objection handling & lead qualification**
- 🗣️ **Chennai-style conversational tone**

---

## 🧠 Use Case

- Corporate meal catering sales
- Event catering follow-ups
- Appointment booking
- Free food sampling coordination
- Lead qualification (location, headcount, interest)

Designed specifically for **Hogest Technologies**, but adaptable to any **voice-based sales or support workflow**.

---

## 🏗️ Architecture Overview

```
Microphone
   ↓ (20ms PCM frames)
Deepgram Flux (STT)
   ↓ (Turn-based transcription)
Speculative LLM Engine (GPT)
   ↓ (Conversation logic)
ElevenLabs TTS
   ↓
Speaker Output (with barge-in)
```

---

## 🧩 Tech Stack

| Layer | Technology |
|-----|-----------|
| Language | Python 3.10+ |
| Speech-to-Text | Deepgram Flux v2 |
| AI Engine | OpenAI GPT-4o-mini |
| Text-to-Speech | ElevenLabs |
| Audio I/O | sounddevice, simpleaudio |
| Streaming | asyncio, WebSockets |

---

## 📦 Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/neha-voice-agent.git
cd neha-voice-agent
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

**⚠️ Never hardcode API keys**

Set the following environment variables:

```bash
export DEEPGRAM_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
export ELEVEN_API_KEY="your_key"
```

Windows (PowerShell):
```powershell
setx DEEPGRAM_API_KEY "your_key"
```

---

## 🎙️ Audio Configuration

Inside the script:

```python
SAMPLE_RATE = 16000
BLOCK_MS = 20
MIC_INDEX = 0
```

To list microphones:
```python
import sounddevice as sd
print(sd.query_devices())
```

---

## ▶️ Run the Agent

```bash
python main.py
```

Neha will:
1. Greet the user
2. Listen continuously
3. Interrupt herself if the user speaks
4. Respond intelligently based on rules

Say **"stop"** to end the session.

---

## 🗣️ Conversation Intelligence

Neha follows strict **telecaller rules**:

- Never mentions AI or bots
- One question at a time
- Handles objections politely
- Detects location & serviceability
- Qualifies leads by headcount
- Offers demo, sampling, or meeting
- Leaves the door open if uninterested

Conversation logic is defined inside:
```python
NEHA_PROMPT = """ ... """
```

---

## 🧪 Advanced Features

### ✅ Speculative LLM Execution
- Starts AI thinking **before** user finishes speaking
- Cancels if user resumes
- Reduces response latency

### ✅ True Barge-In
- AI speech stops instantly when user talks
- Natural human-like interaction

---

## 🧯 Troubleshooting

### No Mic Audio
- Check `MIC_INDEX`
- Install PortAudio

### Audio Lag
- Reduce `BLOCK_MS`
- Use WASAPI exclusive (Windows)

### TTS Delay
- Use `pcm_16000` output
- Keep responses ≤25 words

---

## 📈 Future Enhancements

- 📞 SIP / Telephony integration (TeleCMI, Twilio)
- 🧾 CRM sync
- 📊 Call analytics dashboard
- 🧠 Memory per lead
- 🌍 Multi-language support

---

## ⚠️ Disclaimer

This project is intended for **legitimate business communication only**. Ensure compliance with:
- Local telecalling regulations
- Consent & DND rules
- Data privacy laws

---

## 👩‍💼 Author

**Built for Hogest Technologies, Chennai**  
Voice AI Sales Automation System

---
