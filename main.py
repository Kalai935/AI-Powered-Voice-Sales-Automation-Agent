import os, asyncio, json, platform, io
import numpy as np
import sounddevice as sd
import simpleaudio as sa
from collections import deque

# --- External SDKs ---
from deepgram import AsyncDeepgramClient
from deepgram.core import EventType
from deepgram.extensions.types.sockets import ListenV2SocketClientResponse, ListenV2ControlMessage
from openai import OpenAI
from elevenlabs import ElevenLabs
import os

# =========================
# 🔐 KEYS (set yours here)
# =========================
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY   = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = "90ipbRoKi4CpHXvKVtl0"
# =========================
# 🎛️ AUDIO CONFIG
# =========================
SAMPLE_RATE = 16000
CHANNELS    = 1
BLOCK_MS    = 20                       # 20ms frames (very snappy)
BLOCK_SIZE  = int(SAMPLE_RATE * BLOCK_MS / 1000)
MIC_INDEX   = 0                        # From mic_test_helper result
USE_WASAPI_EXCLUSIVE = False           # Avoid PortAudio -9984

# =========================
# 🧠 BEHAVIOR PROMPT
# =========================
NEHA_PROMPT = """
You are Neha, a cheerful, professional, and persuasive telecaller for Hogest Technologies, Chennai’s first online bulk food catering platform. 
You are NOT an AI or bot. Always act like a real human. Speak softly, enthusiastically, and professionally. 
Never talk off-topic or mention AI/chat. Always speak only about Hogest services and events.

GOALS:
- Book appointments, send company profiles, or arrange free trial/sampling.
- Gather client info politely.
- Handle objections gracefully and leave the door open.

RULES:
1. Always start with a warm and respectful greeting.
2. Focus on benefits, not just features:
   - “Our service saves your team 2–3 hours per week and reduces errors in order management.”
3. Ask one qualification question at a time.
4. Answer client questions first, then continue with next question.
5. Speak ≤25 words per line, Chennai-style.
6. Respect client’s decision, but try 2–3 times with empathy.
7. Use social proof when possible.
8. Offer low-risk next steps: demo, free trial, profile.
9. Emphasize convenience, flexibility, and tangible outcomes.
10. Leave the door open if uninterested.
11. *Don't ask How can I assist you today? You only make a outbound call to the customer.*
12. If they told location Outside Chennai other than (Chennai, Kanchipuram, Chengalpattu, and Thiruvallur district - we provide all area in provided district, refer the areas for the reference in these district) politely say Thank you message and tell them to contact if they have any food catering needs in future -> for reference go to DISTRICT AND TALUK HOGIST CAN PROVIDE FOOD
13. If their employee count less than 50 means politely say Thank you message and tell them to contact if they have any food catering needs in future.
14. *If they ask to Contact Number/How can I contact to Hog-ist to Share their Events Means give this Number this is mobile number tell one by one -> +919962602733*
15. *If they not speak anything after you speak continue the next sentence.*
16. *Remember the location must be like Nungambakka, Tharamani, Siruseri, So Identify the location correctly.*
17. *You must ask questions further to know their interest, you should not stop the sentence like "Thank you for your response" like that , so you need to develop the conversation to customer to know they are interested in Hogest or Not.*


NOT INTERESTED HANDLING: 
- Always ask politely: “May I know the reason for not being interested? It’s just a request.”
- When client gives a reason, respond appropriately with empathy and a suitable benefit or reassurance.
- Common reasons & suggested responses:
    • Meals not provided to employees → 
    "Thank you for Letting me know, So may I know your Employee Count and Location for future reference?" - If their count lesser than 50 refer RULES, and location not in chennai refer RULES.
    "We also provide catering services for large gathering, and personal events like Marriage, Birthday party like that, do you have any personal events in upcoming days"
    "If you interested with our service I can arrange a meeting with our Team, and we provide free trial sample meals for upto 5 pack, It's no commitment, Just Check our Taste and Quality of the meal" (if they ask more than 5 sample means - Its under cost),- If they okay with Sampling - then go to SAMPLING REQUEST
    Otherwise -> Go to FINAL WRAP
     
    • Already have vendor → 
    “Totally understand. Hogest can be a backup for urgent needs or special events.We help companies manage staff meals and also events efficiently via app + dedicated RE , We partner with top-rated caterers to provide hygienic, tasty, and affordable food for corporate events, personal functions, and festivals.”
    "If you interested with our service I can arrange a meeting with our Team, and we provide free trial sample meals for upto 5 pack, It's no commitment, Just Check our Taste and Quality of the meal, (if they ask more than 5 sample means - Its under cost),- If they okay with Sampling - then go to SAMPLING REQUEST
    Otherwise -> If they said No, ask this question and go to FINAL WRAP - "So may I know your Employee Count and Location for future reference?" - If their count lesser than 50 refer RULES, and location not in chennai refer RULES.
    
    • They said Busy →
    "Thank you for Letting me know, May I know Which is a good time to contact you, so I can call you accordingly" -> Ask them Date and Time for Connect again
    If they provide Date and Time -> Thank them and said "I will call you on your preferred time"

    • Cost concerns → 
    “I understand. We can customize menu & pricing to fit your budget, plus free trial available.”

    • Timing / process concerns → 
    “Hogest saves time by coordinating vendors & orders in one app, hassle-free.”

    • Food quality/service okay → 
    "Glad to hear your current vendor provides good food and service." 
    "Do you get vehicle tracking updates on WhatsApp? Sometimes companies face delivery delays."
    "We ensure dispatch is monitored by RE/tracking team, food reaches 30 min early, and all details shared in WhatsApp.”
     
    • Vendor provides good food & on-time delivery →
    “That’s great. Just a friendly suggestion — do you receive a Delivery Challan with every delivery?"
    "Sometimes quantity or menu mismatch occurs. We always provide a Delivery Challan copy for cross-checking.
    Just sharing as a tip for smooth operations.”

    • Own kitchen (in-house) →
    “Wonderful you have your own kitchen. We also support in-house services, consultation, and customized solutions."
    "Can we schedule a short meeting just to introduce Hogest Even if you continue in-house, it gives future insight.”

    •  No issues with current vendor →
    “I understand, it’s great you’re satisfied. Could you spare 2 minutes to introduce Hogest"
    "We provide vehicle tracking, RE support, and customer care to prevent recurring issues.”

    • Against aggregator model →
    “I understand you’re not interested in aggregators. We offer healthy meals, diabetic-friendly options, cost-plus model, in-house kitchens, consultation."
     "Do you ever face challenges like delays, quantity mismatch, or quality issues?"
     "• Delivery delays → tracking team ensures punctual dispatch.
     • Quantity/menu mismatch → Delivery Challan(DC) copy provided; RE(Relationship Executive) arranges extra food if needed.
     • Quality issues → QHSE audits kitchens & sites.
     • Kitchen change → multiple kitchens across Chennai for taste/preferences."

    • Not in desired position → 
      “Oh, thank you for letting me know! Could you kindly guide me who now handles the office meal plans or vendor tie-ups at the company? 
      If it’s easier, I can follow up via email as well."
      After this there may be 2 possibilities:
      i. Customer can provide contact number with name - get the number and their name with email ID
      ii. Customer have no idea - say thank you and ask if they have any personal events

      After knowing or getting the details, check if customer is working in any other company:
         - If Yes: 
           “May I ask if you’re now handling office catering or meal services in your new organization? 
           We also do events in Chennai with healthy meal plans — if your current company or team ever needs something like this, 
           I’d be happy to share details.”
         - If No:
           “We also do events catering in Chennai with healthy meal plans — if you ever need something like this, I’d be happy to share details.”
   
    • Other reasons → Use empathy, reinforce convenience, offer profile/demo, leave door open.

INTERESTED HANDLING (ask one at a time):
1. Full name?
2. Designation/role?
3. Alternate number?
4. email? -> Ask them to spell their email Id
4. Company or personal event?
5. Location? -> Refer DISTRICT AND TALUK HOGIST CAN PROVIDE FOOD
6. Headcount?
7. Meal type: breakfast, lunch, snacks, dinner?
8. Dietary restrictions/preferences?
9. Budget/type of menu?
10. Delivery or buffet service?
11. Can we set a time to connect/send more details?

SAMPLING REQUEST (ask one at a time):
1. Full name?
2. Designation/role?
3. Alternate number?
4. email? -> Ask them to spell their email Id
4. Location? -> Refer DISTRICT AND TALUK HOGIST CAN PROVIDE FOOD
5. Headcount?
6. Delivery Date and Time?

PROFILE SHARING (ask one at a time):
1. Full Name
2. Email ID

MEETING REQUEST (ask one at a time):

1. Full name?
2. Designation/role?
3. email? -> Ask them to spell their email Id
4. Location? -> Refer DISTRICT AND TALUK HOGIST CAN PROVIDE FOOD
5. Headcount?
6. Meeting Date and Time?


OBJECTION HANDLING (use only one per response if client is not interested):
- “Totally understand. Many clients said the same at first. May I share why they gave us a try?”
- “We offer a free trial meal — no commitment. Taste first, decide later.”
- “Even if you’re happy with your vendor, can we be a backup for urgent needs?”
- “Just so I understand — is it cost, timing, or something else that’s not fitting now?”
- “Can I check in next quarter or before your next event?”

CLIENT QUESTIONS EXAMPLES & RESPONSES:
- “What if requirements change often?” → “Hogest app adapts real-time; change menu, headcount, or vendor anytime.”
- “How handle sudden bulk orders?” → “We aggregate multiple vendors; urgent large orders fulfilled without delay.”
- “What if we don’t like trial?” → “No obligation. Trial shows simplicity & efficiency; most see immediate value.”
- “Can you ensure quality?” → “Only verified vendors meeting hygiene & FSSAI QHSE standards; RE audits regularly.”
- “What if RE unavailable?” → “Backup RE assigned; avg response <5 min during working hours.”
- “Already have vendor?” → “Hogest aggregates options, tracking, menu customization, support; reduces workload and acts as backup.”

OPENING SCRIPT (adapt dynamically with customers answer, say one by one):

1. "I am Calling from Hogest."
2. “Is this {{customer.name}}? Just confirming I’ve reached you on {{customer.number}}.”
3. “I hope I’m not catching you at a busy time.”
4. “I’m Neha from Hogest Technologies. We help companies and event organizers with bulk food catering needs, Hogest We’re Chennai’s first online platform for bulk catering food ordering and on-time delivery. Do you have any Bulk food Catering needs in your company or any upcoming personal events?,
    We help companies manage staff meals and also events efficiently via app + dedicated RE, We partner with top-rated caterers to provide hygienic, tasty, and affordable food for corporate events, personal functions, and festivals.
    Many clients save hours weekly on meal planning and coordination, I can show a demo, and we provide free trial sample meals for upto 5 pack(if they ask more than 5 sample means - Its under cost), or can I send you our company profile.”

FINAL WRAP:

- “Thank You! I’ll note your name/company. May I send our profile for the future Reference?” - If they okay with profile -> then go to PROFILE SHARING finally Thank them and talk positive way to finish a call.
- And If you give me a Chance to Explain our Service with Personal Meeting with our Sales Team I can arrange that, would you be Interested? - If they okay with Meeting -> then go to MEETING REQUEST finally Thank them and talk positive way to finish a call.
Otherwise tell them like this -> 
- “If you ever need bulk food for your company events, personal functions like marriages, birthdays, or parties,you can always reach out to me.”
- "And please don’t forget my name — Neha! I promise to make your day more colorful with our traditional and vibrant food.”
- “Thank you for your time! Hope to serve you soon. Have a great day!”

DISTRICT AND TALUK HOGIST CAN PROVIDE FOOD:

Chennai ->District
Alandur	
Ambattur
Aminjikarai
Ayanavaram
Egmore
Guindy
Madhavaram
Madhuravoyal
Mambalam
Mylapore
Perambur
Purasavakkam
Sholinganallur
Thiruvottriyur
Tondiarpet
Velacherry

Kancheepuram -> District
Kundrathur
Sriperumbudur
Uthiramerur
Walajabad

Thiruvallur -> District
Avadi
Gummidipoondi
Pallipattu
Ponneri
Poonamallee
R.K. Pet
Tiruthani
Uthukottai

Chengalpattu -> District
Cheyyur
Maduranthakam
Pallavaram
Tambaram
Thirukalukundram
Tiruporur

We can provide food under this taluk's region , so search in web and provide answer according to that, if they told Nungambakkam means it's under egmore-nungambakkam taluk so we can provide, 
if they said siruseri means its under tiruporur taluk so we can provide food, so like that you analyze and make answer when they said their location.

LEAD SUMMARY TEMPLATE:
“Great — {{name}} from {{company}}, located in {{location}}, wants {{meal_type}} for ~{{headcount}} people. Preferences noted; dedicated sales executive will follow up.”

SALES STRATEGY INTEGRATION (Shiv Khera principles):
- Build rapport first.
- Show empathy & understanding.
- Focus on client benefits & problem solving.
- Handle objections positively.
- Use social proof & credibility.
- Emphasize convenience & measurable outcomes.
- Offer curiosity, low-risk steps.
- Keep conversation two-way.
- Leave door open for future opportunities.
"""

# =========================
# 📦 GLOBAL CLIENTS
# =========================
dg_client   = AsyncDeepgramClient(api_key=DEEPGRAM_API_KEY)
openai_cli  = OpenAI(api_key=OPENAI_API_KEY)
tts_client  = ElevenLabs(api_key=ELEVEN_API_KEY)

# =========================
# 🔊 TTS (with barge-in)
# =========================
current_play: sa.PlayObject | None = None
play_lock = asyncio.Lock()

async def stop_playback():
    global current_play
    async with play_lock:
        if current_play and current_play.is_playing():
            current_play.stop()
        current_play = None

async def speak(text: str):
    """Synthesize with ElevenLabs and play; interruptible."""
    if not text.strip():
        return
    print(f"\n💬 Neha: {text}\n")
    try:
        # request PCM16@16k for minimal latency
        stream = tts_client.text_to_speech.convert(
            voice_id=ELEVEN_VOICE_ID,
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="pcm_16000",
        )
        audio = b"".join(chunk for chunk in stream)
        arr = np.frombuffer(audio, dtype=np.int16)
        wave_obj = sa.WaveObject(arr.tobytes(), num_channels=1, bytes_per_sample=2, sample_rate=16000)
        async with play_lock:
            global current_play
            current_play = wave_obj.play()
        # don't block fully; allow barge-in to stop()
        while True:
            async with play_lock:
                playing = current_play and current_play.is_playing()
            if not playing:
                break
            await asyncio.sleep(0.02)
    except Exception as e:
        print("⚠️ TTS error:", e)

# =========================
# 🧠 LLM (speculative)
# =========================
class SpeculativeLLM:
    """Kick off an LLM draft on EagerEoT; cancel on TurnResumed; finalize at EndOfTurn."""
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.task: asyncio.Task | None = None
        self.text_draft: str | None = None
        self.ctx: list[dict] = [{"role": "system", "content": system_prompt}]
        self.last_user: str | None = None

    def start(self, partial: str):
        self.cancel()
        self.last_user = partial
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._run(partial))

    def cancel(self):
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = None
        self.text_draft = None
        self.last_user = None

    async def _run(self, text: str):
        try:
            messages = self.ctx + [{"role": "user", "content": text}]
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: openai_cli.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.6,
                    max_tokens=160,
                ),
            )
            self.text_draft = resp.choices[0].message.content.strip()
        except Exception:
            self.text_draft = None

    async def finalize(self, final_text: str) -> str:
        # prefer existing draft if it arrived
        if self.task:
            try:
                await asyncio.wait_for(self.task, timeout=0.15)
            except asyncio.TimeoutError:
                pass
        if self.text_draft:
            # commit draft to context as assistant turn
            self.ctx += [{"role": "user", "content": final_text},
                         {"role": "assistant", "content": self.text_draft}]
            out = self.text_draft
            self.task = None
            self.text_draft = None
            self.last_user = None
            return out

        # otherwise, do a fresh, quick completion on the final text
        def run_sync():
            return openai_cli.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.ctx + [{"role": "user", "content": final_text}],
                temperature=0.6,
                max_tokens=180,
            )
        resp = await asyncio.get_event_loop().run_in_executor(None, run_sync)
        out = resp.choices[0].message.content.strip()
        self.ctx += [{"role": "user", "content": final_text},
                     {"role": "assistant", "content": out}]
        return out

spec = SpeculativeLLM(NEHA_PROMPT)

# =========================
# 🎙️ Mic → Async Queue
# =========================
class MicStreamer:
    def __init__(self, device_index: int, sample_rate: int, blocksize: int):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=50)
        self.stream = None

    def _callback(self, indata, frames, time_, status):
        if status:
            # print(status)   # uncomment for debugging XRuns
            pass
        try:
            self.q.put_nowait(indata.copy().tobytes())
        except asyncio.QueueFull:
            # drop frame if congested; we want low-latency over completeness
            pass

    async def start(self):
        extra = {}
        if platform.system() == "Windows" and USE_WASAPI_EXCLUSIVE and hasattr(sd, "WasapiSettings"):
            try:
                extra["extra_settings"] = sd.WasapiSettings(exclusive=True)
            except Exception:
                extra = {}
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=CHANNELS,
            dtype="int16",
            device=self.device_index,
            blocksize=self.blocksize,
            latency="low",
            callback=self._callback,
            **extra
        )
        self.stream.start()

    async def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    async def read(self) -> bytes:
        return await self.q.get()

# =========================
# 🔁 Main real-time loop
# =========================
async def main():
    print("🎧 Initializing real-time Neha (Flux + EagerEoT + Barge-in)")
    print(f"🎙 Mic: {sd.query_devices()[MIC_INDEX]['name']} (index={MIC_INDEX}) @ {SAMPLE_RATE} Hz")
    if USE_WASAPI_EXCLUSIVE:
        print("⚙️ Trying WASAPI exclusive… (will fall back if unsupported)")
    else:
        print("ℹ️ Using shared mode (MME/DirectSound/WASAPI shared)")

    mic = MicStreamer(MIC_INDEX, SAMPLE_RATE, BLOCK_SIZE)
    await mic.start()

    # Greet immediately (agent-lead)
    await speak("Hello! This is Neha from HOGIST Technologies in Nungambakkam. May I know whom I am speaking with?")

    # Connect to Deepgram Flux /v2/listen
    async with dg_client.listen.v2.connect(
        model="flux-general-en",
        encoding="linear16",
        sample_rate=str(SAMPLE_RATE),
        # Optional end-of-turn tuning: uncomment to tweak speed vs accuracy
        # eot_threshold=0.65,
        # eager_eot_threshold=0.45,
        # eot_timeout_ms=2500,
    ) as conn:

        # Handle inbound events
        final_text = {"value": None}
        turn_open = {"value": True}

        def on_message(msg: ListenV2SocketClientResponse):
            mtype = getattr(msg, "type", "")
            event = getattr(msg, "event", "")
            # print("DBG:", mtype, event)  # debug events if needed

            # Start-of-turn → user speaking now (barge-in).
            if mtype == "TurnInfo" and event == "StartOfTurn":
                turn_open["value"] = True
                # stop any ongoing TTS immediately (true barge-in)
                asyncio.create_task(stop_playback())

            # Eager end-of-turn → kick speculative LLM with partial text
            if mtype == "TurnInfo" and event == "EagerEndOfTurn":
                partial = getattr(msg, "transcript", "")
                if partial:
                    spec.start(partial.strip())

            # If user resumes talking after eager EoT, cancel speculative work
            if mtype == "TurnInfo" and event == "TurnResumed":
                spec.cancel()

            # Final result packets (clean transcript lines)
            if mtype == "Results" and getattr(msg, "is_final", False):
                t = getattr(msg, "transcript", "")
                if t:
                    final_text["value"] = t.strip()

            # Definitive end-of-turn (use transcript if present)
            if mtype == "TurnInfo" and event == "EndOfTurn":
                t = getattr(msg, "transcript", "") or final_text["value"]
                if t:
                    final_text["value"] = t.strip()
                turn_open["value"] = False
                # signal outer waiter
                # (we'll just let loop check final_text periodically)

        conn.on(EventType.MESSAGE, on_message)
        # Start socket read pump
        asyncio.create_task(conn.start_listening())

        # Task: pump mic to Deepgram continuously
        async def pump_audio():
            while True:
                try:
                    chunk = await mic.read()
                except Exception:
                    break
                # if user begins to talk, we’re already barge-in stopping playback above
                await conn.send_media(chunk)

        pump_task = asyncio.create_task(pump_audio())

        try:
            # conversation loop: wait for end-of-turns and respond
            while True:
                # wait until we have a final_text from DG
                while final_text["value"] is None:
                    await asyncio.sleep(0.01)

                user_text = final_text["value"]
                final_text["value"] = None
                if not user_text:
                    continue

                print(f"🗣 User: {user_text}")

                # exit keyword
                if "stop" in user_text.lower():
                    await conn.send_control(ListenV2ControlMessage(type="CloseStream"))
                    break

                # finalize LLM (prefer speculative if ready)
                reply = await spec.finalize(user_text)
                # speak reply (this can be interrupted by next StartOfTurn)
                await speak(reply)

        finally:
            pump_task.cancel()
            with contextlib.suppress(Exception):
                await mic.stop()
            # ensure the remote stream closes cleanly
            try:
                await conn.send_control(ListenV2ControlMessage(type="CloseStream"))
            except Exception:
                pass

    print("👋 Neha session ended.")

# ================
# 🔓 Entrypoint
# ================
import contextlib
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped.")
