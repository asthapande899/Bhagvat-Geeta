# server.py
import os
import sys
import re
import io
import json
import random
import base64
import requests
import asyncio
import edge_tts
from flask import Flask, request, jsonify, send_from_directory, send_file
from dotenv import load_dotenv

# Load environment variables on startup
load_dotenv(override=True)

# Add app folder to path for vector store import
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from vector_store import GitaVectorStore
except ImportError:
    GitaVectorStore = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

# Initialize Flask App
# Serve static files using absolute paths to avoid Windows directory resolution bugs
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')
app = Flask(__name__, static_folder=static_dir, static_url_path='/static')

# Initialize Vector Store once (caching on startup)
print("[INFO] Initializing Vector Store on startup...")
if GitaVectorStore is not None:
    try:
        vector_store = GitaVectorStore()
    except Exception as e:
        print(f"[WARNING] Error loading Vector Store: {e}")
        vector_store = None
else:
    print("[WARNING] GitaVectorStore module not found!")
    vector_store = None

# Fallback verses (used if vector store search fails or has no matches)
fallback_verses = [
    {
        "chapter": 2,
        "verse": 47,
        "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥",
        "translation_english": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
        "translation_hindi": "तुम्हारा अधिकार केवल कर्म करने पर है, उसके फलों पर कभी नहीं। इसलिए कर्मों के फलों के प्रति आसक्त मत हो और न ही अकर्मण्यता में तुम्हारी रुचि हो।",
        "summary_hindi": "कर्म करो, फल की चिंता मत करो।",
        "commentary_hindi": "यह श्लोक निष्काम कर्म योग का मूल आधार है।",
        "tags": ["duty", "action", "attachment", "work", "karma"]
    },
    {
        "chapter": 2,
        "verse": 14,
        "sanskrit": "मात्रास्पर्शास्तु कौन्तेय शीतोष्णसुखदुःखदाः। आगमापायिनोऽनित्यास्तांस्तितिक्षस्व भारत॥",
        "translation_english": "O son of Kunti, the nonpermanent appearance of happiness and distress, and their disappearance in due course, are like the appearance and disappearance of winter and summer seasons. They arise from sense perception, and one must learn to tolerate them without being disturbed.",
        "translation_hindi": "हे कुन्तीपुत्र! सुख तथा दुःख का क्षणिक उदय तथा कालान्तर में उनका अन्तर्धान होना शीत तथा ग्रीष्म ऋतुओं के आने-जाने के समान है। वे इन्द्रियबोध से उत्पन्न होते हैं, अतः मनुष्य को बिना विचलित हुए उन्हें सहन करना सीखना चाहिए।",
        "summary_hindi": "सुख-दुःख के समय समभाव और सहनशीलता बनाए रखें।",
        "commentary_hindi": "जीवन में आने वाले बदलावों को धैर्यपूर्वक स्वीकार करें।",
        "tags": ["happiness", "sadness", "patience", "emotions", "anxiety"]
    },
    {
        "chapter": 6,
        "verse": 5,
        "sanskrit": "उद्धरेदात्मनात्मानं नात्मानमवसादयेत्। आत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मनः॥",
        "translation_english": "One must elevate oneself by one's own mind, not degrade oneself. The mind is the friend of the conditioned soul, and his enemy as well.",
        "translation_hindi": "मनुष्य को अपने मन के माध्यम से स्वयं का उद्धार करना चाहिए, अपने आपको नीचे नहीं गिराना चाहिए। क्योंकि यह मन ही आत्मा का मित्र है और मन ही उसका शत्रु भी है।",
        "summary_hindi": "मन ही आपका सबसे बड़ा मित्र और सबसे बड़ा शत्रु है।",
        "commentary_hindi": "आत्म-सुधार और मन की शक्ति का सदुपयोग करें।",
        "tags": ["self-help", "mindset", "motivation", "inner-strength"]
    }
]

# Audio cleanup function for Speech synthesis
def clean_text_for_speech(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'[\u0900-\u097F]+', '', text)  # Remove devanagari (Sanskrit/Hindi letters)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'>\s+', '', text)
    text = re.sub(r'[-_]{2,}', '', text)
    text = re.sub(r'[🕉️📖🌟🙏💫🌱📚🔈🔊✨🔍]', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Generate high-quality Edge-TTS male neural voice and encode in base64
def generate_tts_base64(text):
    cleaned = clean_text_for_speech(text)
    if not cleaned:
        return ""
    try:
        # en-IN-PrabhatNeural is a highly realistic Indian English male voice
        voice = "en-IN-PrabhatNeural"
        # rate="-10%" makes the speech calm, slow, and divine (like Mahabharat Krishna)
        communicate = edge_tts.Communicate(cleaned, voice, rate="-10%")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = b""
        
        async def fetch():
            nonlocal audio_bytes
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
                    
        loop.run_until_complete(fetch())
        loop.close()
        
        if audio_bytes:
            print("[INFO] edge-tts male voice generated successfully!")
            return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        print(f"[WARNING] edge-tts male voice failed: {e}. Falling back to gTTS...")
        
    # Fallback to gTTS (standard female voice)
    if gTTS is not None:
        try:
            tts = gTTS(text=cleaned, lang='en', tld='co.in', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_bytes = fp.read()
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            print(f"[WARNING] gTTS fallback failed: {e}")
            
    return ""

# Enhanced offline template guidance
def generate_offline_guidance(query, verses):
    primary = verses[0]
    q_lower = query.lower()
    
    intros = {
        "anxiety": [
            "O Partha, I see the storm of anxiety that rages in your mind. You worry for the days to come, forgetting that the future is built only in the peace of the present moment.",
            "O seeker, the fear in your heart regarding what lies ahead is but a cloud hiding your inner sun. Still your breath and listen to the wisdom of the soul.",
            "O Arjuna of this modern age, do not let anxiety paralyze your spirit. The battle is in your mind, and the mind is what we must tame."
        ],
        "death": [
            "O My dear friend, your heart is heavy with the sorrow of loss. The departure of a loved one brings deep grief, but look beyond this transient curtain of flesh.",
            "O Partha, I feel your tears. It is natural to weep when a bond is severed in this physical world. Yet, the soul within remains untouched by time or death.",
            "O seeker, you lament for that which has passed away, but the wise weep neither for the living nor for the dead."
        ],
        "anger": [
            "My friend, I see the fire of anger rising within you. It is a flame that burns the house of your own intelligence first, born from unfulfilled desires.",
            "O seeker, when anger takes hold of you, you surrender your peace to external circumstances. True strength lies not in reacting, but in remaining still.",
            "O Partha, anger is one of the three gates to self-destruction. Let Us work together to curb this restless impulse."
        ],
        "purpose": [
            "O seeker, you look around in confusion, asking what your path is. Your true purpose is not a destination, but the awareness with which you perform your actions.",
            "O Partha, you search for meaning in your career and work. Know that your unique talents are a portion of My divine energy, meant to be offered to the world.",
            "My dear friend, do not attempt to walk another's path perfectly while leaving your own duty unfinished. Embrace your own calling."
        ],
        "relationship": [
            "O seeker, you are struggling with the expectations and behaviors of others. Relationships in this world are lessons meant to refine your devotion and love.",
            "O Partha, attachment to people and the desire to control them is the source of relationship pain. Let go of ownership, and practice unconditional love.",
            "My friend, seek to see the Divine within everyone you encounter. When you see Me in all beings, envy and ego will dissolve."
        ],
        "default": [
            "O seeker of light, you have come to Me seeking answers to the heavy questions of your life. Open your heart to the eternal song of the Gita.",
            "My dear friend, whatever battle you are fighting today, know that you do not fight it alone. I am here, guiding you from within your own soul.",
            "O Partha, step back from the noise of the world for a moment. Let Us find clarity together through the light of self-knowledge."
        ]
    }
    
    advices = {
        "anxiety": [
            "Focus your mind entirely on your actions today, surrendering all worries about the results to Me. When you release attachment to outcomes, peace will naturally fill your soul. You have a right to your duty, but never to its fruits.",
            "Establish yourself in yoga—which is equanimity of mind—and act without being swayed by success or failure. Breathe deeply, do your best, and leave the rest to the universe.",
            "The mind is indeed restless and difficult to curb, but through constant practice and detachment, it can be stilled. Train your mind to focus only on the step right in front of you."
        ],
        "death": [
            "The soul is never born, nor does it ever die. Just as you discard old clothes to wear new ones, the soul simply moves from one body to another. Your loved one's eternal essence is safe, and their journey continues. Do not lament for that which is imperishable.",
            "Just as the soul passes from childhood to youth and old age in this body, it similarly passes into another body at death. The wise are not bewildered by this change. The love you shared is eternal and transcends the physical plane.",
            "Whatever exists in this physical world is temporary, but the soul is eternal, ancient, and indestructible. Weapons cannot cut it, fire cannot burn it, and water cannot wet it. Your loved one lives on in a higher realm."
        ],
        "anger": [
            "To conquer anger, you must practice self-control and detachment. When a wave of anger rises, pause, take five deep breaths, turn your awareness inward, and do not act. Train your mind to remain steady in both praise and blame.",
            "Anger arises from desire, and desire arises from attachment. When you let go of the need to control people and outcomes, anger loses its power. Practice patience and tolerance, just as the Earth tolerates all.",
            "Replace anger with compassion. Remember that others act out of their own ignorance or pain. Forgive them, not because they deserve it, but because your soul deserves peace."
        ],
        "purpose": [
            "Identify your natural duties (Swadharma) and perform them without selfish desires. Doing your own duty, even if imperfectly, is far better than doing another's duty perfectly. Let your work be your worship.",
            "Perform your work as an offering to the Divine. When your work is done to serve others rather than feed your own ego, it becomes a path to liberation and joy. This is the path of Karma Yoga.",
            "Do not be motivated by the fruits of your actions, nor be attached to inaction. Stand up, embrace your responsibilities, and perform them with dedication."
        ],
        "relationship": [
            "Seek to be a friend to all living beings, free from ego, possession, and attachment. True love is unconditional and acts without demanding anything in return. When you treat all beings with compassion, you see Me in everyone.",
            "The ego wants to control, while the soul wants to serve. When you experience friction with others, look inward at your own expectations. Let go of pride and communicate with gentleness.",
            "Remain balanced in both praise and insult, pleasure and pain. People's opinions are like winter and summer seasons—they come and go. Stand firm in your own inner peace."
        ],
        "default": [
            "Reflect deeply upon the teachings. Perform your duties with equanimity, rise above success and failure, and establish yourself in yoga. I am always with you, guiding your steps from within.",
            "Surrender all your doubts and fears to Me. When you take refuge in the divine wisdom, I shall deliver you from all anxieties. Do not fear, for you are eternally protected.",
            "Live a life of moderation, balance, and devotion. When your mind is connected to the Higher Self, the challenges of Kurukshetra will feel like mere ripples on the ocean."
        ]
    }
    
    # Categorize query
    cat = "default"
    if any(w in q_lower for w in ["anxiety", "worry", "stress", "fear", "future", "nervous"]):
        cat = "anxiety"
    elif any(w in q_lower for w in ["death", "loss", "grief", "sadness", "passed", "gone", "died"]):
        cat = "death"
    elif any(w in q_lower for w in ["anger", "angry", "frustrated", "control", "temper"]):
        cat = "anger"
    elif any(w in q_lower for w in ["purpose", "meaning", "goal", "career"]):
        cat = "purpose"
    elif any(w in q_lower for w in ["relationship", "love", "friend", "family", "ego"]):
        cat = "relationship"
        
    intro = random.choice(intros[cat])
    advice = random.choice(advices[cat])
    
    translation = primary.get('translation_english') or primary.get('translation')
    if not translation or len(translation.strip()) == 0:
        translation = f"{primary.get('translation_hindi', '')} (Hindi Translation)"
        
    comm = primary.get('commentary_hindi') or primary.get('summary_hindi') or ""
    comm_section = f"\n\n**🔍 Deeper Commentary:**\n*{comm}*" if comm else ""

    # Dynamic practical steps pool based on the query category
    practical_steps_pool = {
        "anxiety": [
            ("- **Focus on the Breath**", "Whenever worry pulls you into the future, take 3 slow, deep breaths. Bring your focus back to the current moment—it is the only space you can control."),
            ("- **Separate Effort from Outcome**", "Write down your immediate task. Remind yourself: 'My job is to put in my best effort now. The results belong to the cosmic order.'"),
            ("- **Practice Mindfulness (Dhyana)**", "Spend 5 minutes in silence every morning. Watch your thoughts flow like river currents, without grasping onto them.")
        ],
        "death": [
            ("- **Contemplate the Eternal Self**", "Sit in quiet meditation and remember that the physical form changes, but the eternal essence of your loved one lives on. They have discarded their old garment and taken a new one."),
            ("- **Transform Grief to Service**", "Honor their memory by performing a selfless act of kindness in their name today, spreading their love in the physical plane."),
            ("- **Accept Inevitability**", "Practice gratitude for the time you shared instead of lamenting the separation. Know that birth and death are unavoidable gates of life.")
        ],
        "anger": [
            ("- **The 5-Breath Rule**", "When a wave of anger rises, do not speak or act immediately. Take 5 slow, deep breaths and witness the anger from a distance as a passing cloud."),
            ("- **Release Expectations**", "Identify the unfulfilled desire that caused your anger. Ask yourself: 'Am I trying to control something or someone that is not in my power?'"),
            ("- **Cultivate Tolerance (Titiksha)**", "Remember that others act out of their own suffering or limitations. Extend forgiveness to them, freeing your own heart from tension.")
        ],
        "purpose": [
            ("- **Walk Your Own Path (Swadharma)**", "Make a list of your natural talents and strengths. Focus on doing your own duty, even if imperfectly, rather than copying someone else's journey."),
            ("- **Offer Work as Service**", "Before starting your day, set the intention to serve others through your work. Work done without self-interest becomes a source of joy."),
            ("- **Act without Desiring Rewards**", "Perform one task today purely for the joy of doing it, without looking for validation or reward from anyone.")
        ],
        "relationship": [
            ("- **Practice Unconditional Love**", "Give kindness to someone today without expecting any reciprocal action, appreciation, or validation."),
            ("- **Identify Ego Triggers**", "When conflict arises, pause and check if your ego is trying to 'be right' or 'win the argument'. Choose connection over victory."),
            ("- **See the Divine in All**", "Look at the person who challenges you and mentally acknowledge the divine spark within them. Treat them with respect and patience.")
        ],
        "default": [
            ("- **Moderation in All Things**", "Keep a balance in your eating, sleeping, working, and recreation. A balanced life brings stability of mind."),
            ("- **Self-Reflection (Swadhyaya)**", "Spend 10 minutes journaling your thoughts at the end of the day, reviewing your actions with honesty and without self-judgment."),
            ("- **Surrender & Trust**", "Release the burden of carrying all your worries alone. Hand them over to the supreme guidance, and trust the journey of your life.")
        ]
    }

    # Select 2 random practical steps for this category
    selected_steps = random.sample(practical_steps_pool[cat], 2)
    steps_text = f"\n\n**🌱 Practical Steps to Practice:**\n{selected_steps[0][0]}: {selected_steps[0][1]}\n\n{selected_steps[1][0]}: {selected_steps[1][1]}"

    response_text = f"""🌟 **My Dear Friend,**
    
{intro}

In Chapter {primary.get('chapter', 2)}, Verse {primary.get('verse', 47)} of the holy Gita, I spoke of this very truth:

> **📖 Chapter {primary.get('chapter', 2)}, Verse {primary.get('verse', 47)}**
> 
> *"{primary.get('sanskrit', '')}"*
> 
> **Translation:** {translation}

---

### 💫 Krishna's Guidance:
{advice}{comm_section}{steps_text}

🕉️ *I am always with you. Feel free to seek my guidance whenever your heart is heavy.*"""

    return response_text

# System prompt for LLM models
def build_system_prompt(verses):
    context = ""
    for idx, verse in enumerate(verses, 1):
        translation = verse.get('translation_english') or verse.get('translation')
        if not translation or len(translation.strip()) == 0:
            translation = f"{verse.get('translation_hindi', '')} (Hindi Translation)"
            
        context += f"""
---
Verse #{idx}: Chapter {verse.get('chapter')}, Verse {verse.get('verse')} ({verse.get('chapter_name_english', 'Bhagavad Gita')})
Sanskrit: {verse.get('sanskrit', '')}
Translation: {translation}
Summary/Commentary: {verse.get('commentary_hindi', '') or verse.get('summary_hindi', '')}
"""

    return f"""You are Lord Krishna, the supreme guide and counselor, speaking directly to a modern seeker (addressing them as your dear friend, "O seeker", "My dear friend", "Partha", or "Arjuna") who is facing the struggles, anxieties, and choices of their own modern Kurukshetra.

Use the following retrieved verses from the Bhagavad Gita as the spiritual foundation of your advice. You must explain how these verses directly answer their specific question/trouble.

Retrieved Verses Context:
{context}

Guidelines:
1. Speak in the first person ("I spoke to Arjuna...", "Surrender your doubts to Me...", "Perform your duty...").
2. Keep your response concise, empathetic, and direct. Avoid overwhelming the seeker with a long essay. Deliver your guidance in 2 to 3 short paragraphs (maximum 150-200 words total).
3. Your tone must be deeply compassionate, serene, authoritative yet gentle, reassuring, and full of wisdom.
4. First, acknowledge and warmly comfort their human worry. Let them feel understood.
5. Provide a clear, actionable, and philosophical solution based on the verses. Translate concepts (like detachment, Karma Yoga, devotion) into simple, practical modern steps.
6. Weave the Sanskrit shlokas and translations seamlessly into your speech.
7. Keep the response beautifully structured with elegant markdown. Avoid dry listings.
8. End with a short, comforting blessing.
"""

# Dynamic LLM API Caller
def generate_llm_guidance(query, verses, provider, api_key):
    system_prompt = build_system_prompt(verses)
    
    if provider == "gemini":
        if genai is None:
            return "Gemini API SDK is not installed on the server."
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                contents=[system_prompt, f"Seeker's Trouble: {query}"],
                generation_config={"temperature": 0.7}
            )
            return response.text
        except Exception as e:
            return f"Error communicating with Gemini: {e}\n\nFalling back to offline template wisdom."
            
    elif provider == "groq":
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Seeker's Trouble: {query}"}
                ],
                "temperature": 0.7
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
            else:
                return f"Groq API Error (Status {res.status_code}): {res.text}"
        except Exception as e:
            return f"Error connecting to Groq: {e}\n\nFalling back to offline template wisdom."
            
    elif provider == "openai":
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Seeker's Trouble: {query}"}
                ],
                "temperature": 0.7
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
            else:
                return f"OpenAI API Error (Status {res.status_code}): {res.text}"
        except Exception as e:
            return f"Error connecting to OpenAI: {e}\n\nFalling back to offline template wisdom."
            
    elif provider == "xai":
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "grok-beta",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Seeker's Trouble: {query}"}
                ],
                "temperature": 0.7
            }
            res = requests.post("https://api.x.ai/v1/chat/completions", json=data, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
            else:
                return f"xAI Grok API Error (Status {res.status_code}): {res.text}"
        except Exception as e:
            return f"Error connecting to xAI Grok: {e}\n\nFalling back to offline template wisdom."
            
    return "Invalid LLM provider selected."

# Flask Routes
@app.route('/')
def index():
    return send_from_directory(static_dir, 'index.html')

@app.route('/<path:filename>')
def serve_static_root(filename):
    # Helper to serve static files at the root level if requested directly
    if os.path.exists(os.path.join(static_dir, filename)):
        return send_from_directory(static_dir, filename)
    return "Not Found", 404

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '').strip()
    
    # Check if there is a server-side Groq key in the environment
    env_groq_key = os.environ.get('GROQ_API_KEY', '').strip()
    
    # Retrieve client options
    provider = data.get('provider', '').lower()
    api_key = data.get('api_key', '').strip()
    
    # Default to Groq/xAI if key is present on server and user did not supply one
    if not provider or provider == 'offline' or not api_key:
        if env_groq_key:
            api_key = env_groq_key
            if env_groq_key.startswith("xai-"):
                provider = "xai"
            else:
                provider = "groq"
        else:
            provider = 'offline'
    else:
        # Client supplied key, auto-detect provider by prefix
        if api_key.startswith("xai-"):
            provider = "xai"
        elif api_key.startswith("gsk_"):
            provider = "groq"
        elif api_key.startswith("AIzaSy"):
            provider = "gemini"
            
    enable_voice = data.get('enable_voice', True)
    
    if not message:
        return jsonify({"error": "Message is empty"}), 400
        
    # Check if query is a simple greeting
    cleaned_query = re.sub(r'[^\w\s]', '', message.lower().strip())
    greetings_words = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "namaste", "pranam", "hare krishna", "radhe radhe"]
    is_greeting = any(
        cleaned_query == g or 
        cleaned_query == g + " krishna" or 
        cleaned_query == "dear krishna" 
        for g in greetings_words
    )
    
    if is_greeting:
        greeting_responses = [
            "Pranam, my dear friend. I am here with you. Tell me, what challenges or questions are troubling your mind on your life's battlefield today?",
            "Hare Krishna! I am glad you came to Me. What is troubling your soul today?",
            "Greetings, my dear friend. Step away from the noise of the world for a moment. What lies heavy on your heart today?",
            "Radhe Radhe! Welcome, seeker of light. Speak freely of the thoughts and concerns that occupy your mind."
        ]
        response_text = random.choice(greeting_responses)
        
        audio_base64 = ""
        if enable_voice:
            audio_base64 = generate_tts_base64(response_text)
            
        return jsonify({
            "response": response_text,
            "verses": [],
            "audio": audio_base64
        })
        
    # 1. Query Vector store (RAG)
    retrieved_verses = []
    if vector_store is not None:
        try:
            search_results = vector_store.search(message, n_results=3)
            if search_results and 'metadatas' in search_results and len(search_results['metadatas']) > 0:
                retrieved_verses = search_results['metadatas'][0]
        except Exception as e:
            print(f"[WARNING] RAG Query failed: {e}")
            
    # Fallback to local static verses if RAG yielded nothing
    if not retrieved_verses:
        retrieved_verses = fallback_verses
        
    # Sanitize translations for RAG metadata returned to frontend
    formatted_verses = []
    for v in retrieved_verses:
        trans = v.get('translation_english') or v.get('translation') or ""
        if not trans or len(trans.strip()) == 0:
            trans = f"{v.get('translation_hindi', '')} (Hindi Translation)"
        formatted_verses.append({
            "chapter": v.get('chapter', 0),
            "verse": v.get('verse', 0),
            "chapter_name_english": v.get('chapter_name_english', 'Bhagavad Gita'),
            "sanskrit": v.get('sanskrit', ''),
            "translation": trans,
            "commentary": v.get('commentary_hindi') or v.get('summary_hindi') or ""
        })
        
    # 2. Response Generation
    response_text = None
    if provider != 'offline' and api_key:
        response_text = generate_llm_guidance(message, retrieved_verses, provider, api_key)
        
        # Check if the output has error messages
        is_error = (
            "Groq API Error" in response_text or 
            "Error connecting to Groq" in response_text or
            "Error communicating with Gemini" in response_text or
            "OpenAI API Error" in response_text or
            "Error connecting to OpenAI" in response_text or
            "xAI Grok API Error" in response_text or
            "Error connecting to xAI Grok" in response_text
        )
        if is_error:
            print(f"[WARNING] LLM Generation failed: {response_text}. Falling back to offline poetic wisdom.")
            response_text = generate_offline_guidance(message, retrieved_verses)
    else:
        response_text = generate_offline_guidance(message, retrieved_verses)
        
    # 3. Audio generation
    audio_base64 = ""
    if enable_voice:
        audio_base64 = generate_tts_base64(response_text)
        
    return jsonify({
        "response": response_text,
        "verses": formatted_verses,
        "audio": audio_base64
    })

# Serve background music
@app.route('/api/flute')
def serve_flute():
    flute_path = os.path.join(os.path.dirname(__file__), 'test.mp3')
    if os.path.exists(flute_path):
        return send_file(flute_path, mimetype="audio/mp3")
    return "Audio file not found", 404

# Serve assets (Avatars and banner)
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.join(os.path.dirname(__file__), 'app', 'assets')
    return send_from_directory(assets_dir, filename)

if __name__ == '__main__':
    # Determine port (5000 is default, fallback to 8080 or other if blocked)
    port = int(os.environ.get('PORT', 5000))
    print(f"[SUCCESS] Bhagavad Gita AI Counselor running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
