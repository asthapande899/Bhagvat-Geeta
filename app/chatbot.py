# app/chatbot.py
import streamlit as st
import random
import os
import sys
import re
import io

# Add parent directory to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import custom vector store
try:
    from app.vector_store import GitaVectorStore
except ImportError:
    try:
        from vector_store import GitaVectorStore
    except ImportError:
        GitaVectorStore = None

# Safely import Gemini API
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Safely import Google Text-To-Speech
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

# Hardcoded fallback verses (in case vector store fails)
fallback_static_verses = [
    {
        "chapter": 2,
        "verse": 47,
        "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन। मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥",
        "translation_english": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
        "translation_hindi": "तुम्हारा अधिकार केवल कर्म करने पर है, उसके फलों पर कभी नहीं। इसलिए कर्मों के फलों के प्रति आसक्त मत हो और न ही अकर्मण्यता में तुम्हारी रुचि हो।",
        "summary_hindi": "कर्म करो, फल की चिंता मत करो।",
        "commentary_hindi": "यह श्लोक निष्काम कर्म योग का मूल आधार है।",
        "tags": "duty, action, attachment, work, karma"
    },
    {
        "chapter": 2,
        "verse": 14,
        "sanskrit": "मात्रास्पर्शास्तु कौन्तेय शीतोष्णसुखदुःखदाः। आगमापायिनोऽनित्यास्तांस्तितिक्षस्व भारत॥",
        "translation_english": "O son of Kunti, the nonpermanent appearance of happiness and distress, and their disappearance in due course, are like the appearance and disappearance of winter and summer seasons. They arise from sense perception, and one must learn to tolerate them without being disturbed.",
        "translation_hindi": "हे कुन्तीपुत्र! सुख तथा दुःख का क्षणिक उदय तथा कालान्तर में उनका अन्तर्धान होना शीत तथा ग्रीष्म ऋतुओं के आने-जाने के समान है। वे इन्द्रियबोध से उत्पन्न होते हैं, अतः मनुष्य को बिना विचलित हुए उन्हें सहन करना सीखना चाहिए।",
        "summary_hindi": "सुख-दुःख के समय समभाव और सहनशीलता बनाए रखें।",
        "commentary_hindi": "जीवन में आने वाले बदलावों को धैर्यपूर्वक स्वीकार करें।",
        "tags": "happiness, sadness, patience, emotions, anxiety"
    },
    {
        "chapter": 6,
        "verse": 5,
        "sanskrit": "उद्धरेदात्मनात्मानं नात्मानमवसादयेत्। आत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मनः॥",
        "translation_english": "One must elevate oneself by one's own mind, not degrade oneself. The mind is the friend of the conditioned soul, and his enemy as well.",
        "translation_hindi": "मनुष्य को अपने मन के माध्यम से स्वयं का उद्धार करना चाहिए, अपने आपको नीचे नहीं गिराना चाहिए। क्योंकि यह मन ही आत्मा का मित्र है और मन ही उसका शत्रु भी है।",
        "summary_hindi": "मन ही आपका सबसे बड़ा मित्र और सबसे बड़ा शत्रु है।",
        "commentary_hindi": "आत्म-सुधार और मन की शक्ति का सदुपयोग करें।",
        "tags": "self-help, mindset, motivation, inner-strength"
    }
]

# Audio cleanup function
def clean_text_for_speech(text):
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'[\u0900-\u097F]+', '', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'>\s+', '', text)
    text = re.sub(r'[-_]{2,}', '', text)
    text = re.sub(r'[🕉️📖🌟🙏💫🌱📚🔈🔊✨]', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Audio speech generator (Cached)
@st.cache_data(show_spinner=False)
def generate_speech_audio(text):
    if gTTS is None:
        return None
    try:
        cleaned = clean_text_for_speech(text)
        if not cleaned:
            return None
        tts = gTTS(text=cleaned, lang='en', tld='co.in', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        return None

# Page Configuration
st.set_page_config(
    page_title="Bhagavad Gita AI Counselor",
    page_icon="🕉️",
    layout="wide"
)

# Deep spiritual aesthetics theme (Dark mode with gold and saffron details)
# Note: Indentation removed from HTML/CSS block to prevent Streamlit rendering it as a code element.
st.markdown("""<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
<style>
/* Main Background */
.stApp {
    background: linear-gradient(135deg, #070913 0%, #121324 50%, #080911 100%) !important;
    font-family: 'Outfit', sans-serif;
}

/* Force readable color globally for all basic text elements */
.stApp p, .stApp span, .stApp div, .stApp label, .stApp li {
    color: #f8fafc !important;
}

/* Headings with Gold/Saffron details */
h1, h2, h3, h4 {
    font-family: 'Cinzel', serif !important;
    color: #f59e0b !important;
    text-shadow: 0px 0px 10px rgba(245, 158, 11, 0.35);
    font-weight: 700 !important;
}

/* Custom Divine Card */
.divine-card {
    background: rgba(20, 21, 38, 0.7);
    border: 1px solid rgba(245, 158, 11, 0.25);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    margin-bottom: 25px;
}

.divine-quote {
    font-style: italic;
    font-size: 1.15rem;
    color: #fef08a !important;
    line-height: 1.6;
    text-align: center;
    margin: 15px 0;
}

/* Gold Divider */
.gold-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #f59e0b, transparent);
    margin: 20px 0;
}

/* Chat Messages overriding default grey fonts */
.stChatMessage {
    background-color: rgba(24, 25, 48, 0.75) !important;
    border: 1px solid rgba(245, 158, 11, 0.2) !important;
    border-radius: 14px !important;
    padding: 18px !important;
    margin-bottom: 15px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
}

.stChatMessage p, .stChatMessage span, .stChatMessage div {
    color: #f8fafc !important;
    font-size: 1.05rem !important;
    line-height: 1.6 !important;
}

/* Expanders gold border */
.streamlit-expanderHeader {
    background-color: rgba(245, 158, 11, 0.05) !important;
    border: 1px solid rgba(245, 158, 11, 0.15) !important;
    border-radius: 8px !important;
}

/* Audio player custom fit */
div.stAudio {
    margin-top: 10px;
    max-width: 320px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0c0d1b !important;
    border-right: 1px solid rgba(245, 158, 11, 0.2) !important;
}

section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] label {
    color: #e2e8f0 !important;
}

/* Inputs & Buttons */
div[data-baseweb="input"] {
    background-color: #16182d !important;
    border: 1px solid rgba(245, 158, 11, 0.25) !important;
    border-radius: 8px !important;
}

button {
    border-color: rgba(245, 158, 11, 0.4) !important;
    color: #f59e0b !important;
    background-color: transparent !important;
}

button:hover {
    background-color: rgba(245, 158, 11, 0.1) !important;
    border-color: #f59e0b !important;
}
</style>""", unsafe_allow_html=True)

# Cache vector store load
@st.cache_resource
def get_vector_store():
    if GitaVectorStore is not None:
        try:
            return GitaVectorStore()
        except Exception as e:
            st.sidebar.warning(f"ChromaDB not fully loaded. System will fallback to local parsing: {e}")
            return None
    return None

vector_store = get_vector_store()

# Sidebar: Controls and Info
with st.sidebar:
    st.image("app/assets/krishna_banner.png" if os.path.exists("app/assets/krishna_banner.png") else "🕉️", use_column_width=True)
    st.markdown("<h2 style='text-align: center; font-size: 1.6rem;'>Settings & Blessings</h2>", unsafe_allow_html=True)
    
    # Secure Gemini API Key Input
    gemini_key = st.text_input(
        "Enter Gemini API Key (Recommended)", 
        type="password", 
        help="Paste your free Gemini key for highly creative, personalized, and flowy answers where Krishna answers your exact problems directly.",
        key="gemini_api_key"
    )
    
    # Fast access instructions for free key
    st.markdown("""
    <div style='background-color: rgba(245,158,11,0.08); padding: 10px; border-radius: 6px; border: 1px solid rgba(245,158,11,0.2); font-size: 0.85rem;'>
    💡 <b>Tip:</b> Get a free API key in 30 seconds from <a href="https://aistudio.google.com/" target="_blank" style="color:#f59e0b; font-weight:bold;">Google AI Studio</a> to unlock creative answers.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
    
    # Audio response options
    enable_audio = st.toggle("🔈 Enable Voice Answers (Krishna Speaks)", value=True, key="voice_enabled")
    
    # Background music playing
    if os.path.exists("test.mp3"):
        st.markdown("<p style='font-size: 0.9rem; color: #a1a1aa;'>🧘 Meditative Background Flute</p>", unsafe_allow_html=True)
        st.audio("test.mp3", format="audio/mp3", loop=True)
        st.caption("Press play on the player above to loop a soft flute track during your chat.")
        
    st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    ### 📖 Key Teachings to Explore
    - *"I feel stressed about my exams/career"*
    - *"How do I deal with the loss of a parent?"*
    - *"How can I control my short temper?"*
    - *"What is my true path and duty in life?"*
    """)
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #a1a1aa; font-size: 0.8rem;'>Made with devotion using AI & the eternal wisdom of the Gita 🙏</div>", unsafe_allow_html=True)

# Header Title Block
st.markdown("""
<div class='divine-card'>
    <h1 style='text-align: center; margin: 0; font-size: 2.5rem;'>🕉️ Bhagavad Gita AI Counselor</h1>
    <div class='gold-divider'></div>
    <div class='divine-quote'>
        "When Arjuna was confused on the battlefield of life, Krishna answered his questions with eternal wisdom.<br>
        Now, ask your questions and find guidance through the timeless teachings of the Bhagavad Gita."
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "🙏 Welcome, seeker of truth. I am here to share the timeless path of the Bhagavad Gita with you. Tell me, what challenges or questions are troubling your mind on your life's battlefield today?"
        }
    ]

# Avatar Paths
krishna_avatar = "app/assets/krishna_avatar.png" if os.path.exists("app/assets/krishna_avatar.png") else None
seeker_avatar = "app/assets/seeker_avatar.png" if os.path.exists("app/assets/seeker_avatar.png") else None

# Render Chat History
for msg in st.session_state.messages:
    role = msg["role"]
    avatar = krishna_avatar if role == "assistant" else seeker_avatar
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])
        # If TTS was generated, render the player
        if role == "assistant" and "audio" in msg and msg["audio"] is not None:
            st.audio(msg["audio"], format="audio/mp3")

# LLM RAG Response Generator
def generate_llm_guidance(query, verses, api_key):
    if genai is None:
        return "LLM integration currently unavailable."
    
    # Configure API
    genai.configure(api_key=api_key)
    
    # Format retrieved verses as context
    context = ""
    for idx, verse in enumerate(verses, 1):
        # Resolve translation, fallback to Hindi if English translation is blank
        translation = verse.get('translation_english')
        if not translation or len(translation.strip()) == 0:
            translation = f"{verse.get('translation_hindi', '')} (Hindi Translation)"
            
        context += f"""
---
Verse #{idx}: Chapter {verse.get('chapter')}, Verse {verse.get('verse')} ({verse.get('chapter_name_english', 'Bhagavad Gita')})
Sanskrit: {verse.get('sanskrit', '')}
Translation: {translation}
Summary/Commentary: {verse.get('commentary_hindi', '') or verse.get('summary_hindi', '')}
"""

    system_prompt = f"""You are Lord Krishna, the supreme guide and counselor, speaking directly to a modern seeker (addressing them as your dear friend, "O seeker", "My dear friend", "Partha", or "Arjuna") who is facing the struggles, anxieties, and choices of their own modern Kurukshetra.

Use the following retrieved verses from the Bhagavad Gita as the spiritual foundation of your advice. You must explain how these verses directly answer their specific question/trouble.

Retrieved Verses Context:
{context}

Guidelines:
1. Speak in the first person ("I spoke to Arjuna...", "Surrender your doubts to Me...", "Perform your duty...").
2. Your tone must be deeply compassionate, serene, authoritative yet gentle, reassuring, and full of wisdom.
3. First, acknowledge and warmly comfort their human worry. Let them feel understood.
4. Provide a clear, actionable, and philosophical solution based on the verses. Translate concepts (like detachment, Karma Yoga, devotion) into simple, practical modern steps.
5. Weave the Sanskrit shlokas and translations seamlessly into your speech.
6. Keep the response beautifully structured with elegant markdown. Avoid dry listings.
7. End with a comforting blessing.
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            contents=[system_prompt, f"Seeker's Trouble: {query}"],
            generation_config={"temperature": 0.7}
        )
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini: {e}\n\nFalling back to offline template wisdom."

# Fallback Offline Generator (Enhanced to sound much more custom and poetic)
def generate_offline_guidance(query, verses):
    if not verses:
        verses = fallback_static_verses
        
    primary_meta = verses[0]
    q_lower = query.lower()
    
    # Intros variations
    intro_anxiety = [
        "O Partha, I see the storm of anxiety that rages in your mind. You worry for the days to come, forgetting that the future is built only in the peace of the present moment.",
        "O seeker, the fear in your heart regarding what lies ahead is but a cloud hiding your inner sun. Still your breath and listen to the wisdom of the soul.",
        "O Arjuna of this modern age, do not let anxiety paralyze your spirit. The battle is in your mind, and the mind is what we must tame."
    ]
    
    intro_death = [
        "O My dear friend, your heart is heavy with the sorrow of loss. The departure of a loved one brings deep grief, but look beyond this transient curtain of flesh.",
        "O Partha, I feel your tears. It is natural to weep when a bond is severed in this physical world. Yet, the soul within remains untouched by time or death.",
        "O seeker, you lament for that which has passed away, but the wise weep neither for the living nor for the dead."
    ]
    
    intro_anger = [
        "My friend, I see the fire of anger rising within you. It is a flame that burns the house of your own intelligence first, born from unfulfilled desires.",
        "O seeker, when anger takes hold of you, you surrender your peace to external circumstances. True strength lies not in reacting, but in remaining still.",
        "O Partha, anger is one of the three gates to self-destruction. Let Us work together to curb this restless impulse."
    ]
    
    intro_purpose = [
        "O seeker, you look around in confusion, asking what your path is. Your true purpose is not a destination, but the awareness with which you perform your actions.",
        "O Partha, you search for meaning in your career and work. Know that your unique talents are a portion of My divine energy, meant to be offered to the world.",
        "My dear friend, do not attempt to walk another's path perfectly while leaving your own duty unfinished. Embrace your own calling."
    ]
    
    intro_relationship = [
        "O seeker, you are struggling with the expectations and behaviors of others. Relationships in this world are lessons meant to refine your devotion and love.",
        "O Partha, attachment to people and the desire to control them is the source of relationship pain. Let go of ownership, and practice unconditional love.",
        "My friend, seek to see the Divine within everyone you encounter. When you see Me in all beings, envy and ego will dissolve."
    ]
    
    intro_default = [
        "O seeker of light, you have come to Me seeking answers to the heavy questions of your life. Open your heart to the eternal song of the Gita.",
        "My dear friend, whatever battle you are fighting today, know that you do not fight it alone. I am here, guiding you from within your own soul.",
        "O Partha, step back from the noise of the world for a moment. Let Us find clarity together through the light of self-knowledge."
    ]
    
    # Custom Advice Variations
    advice_anxiety = [
        "Focus your mind entirely on your actions today, surrendering all worries about the results to Me. When you release attachment to outcomes, peace will naturally fill your soul. You have a right to your duty, but never to its fruits.",
        "Establish yourself in yoga—which is equanimity of mind—and act without being swayed by success or failure. Breathe deeply, do your best, and leave the rest to the universe.",
        "The mind is indeed restless and difficult to curb, but through constant practice and detachment, it can be stilled. Train your mind to focus only on the step right in front of you."
    ]
    
    advice_death = [
        "The soul is never born, nor does it ever die. Just as you discard old clothes to wear new ones, the soul simply moves from one body to another. Your loved one's eternal essence is safe, and their journey continues. Do not lament for that which is imperishable.",
        "Just as the soul passes from childhood to youth and old age in this body, it similarly passes into another body at death. The wise are not bewildered by this change. The love you shared is eternal and transcends the physical plane.",
        "Whatever exists in this physical world is temporary, but the soul is eternal, ancient, and indestructible. Weapons cannot cut it, fire cannot burn it, and water cannot wet it. Your loved one lives on in a higher realm."
    ]
    
    advice_anger = [
        "To conquer anger, you must practice self-control and detachment. When a wave of anger rises, pause, take five deep breaths, turn your awareness inward, and do not act. Train your mind to remain steady in both praise and blame.",
        "Anger arises from desire, and desire arises from attachment. When you let go of the need to control people and outcomes, anger loses its power. Practice patience and tolerance, just as the Earth tolerates all.",
        "Replace anger with compassion. Remember that others act out of their own ignorance or pain. Forgive them, not because they deserve it, but because your soul deserves peace."
    ]
    
    advice_purpose = [
        "Identify your natural duties (Swadharma) and perform them without selfish desires. Doing your own duty, even if imperfectly, is far better than doing another's duty perfectly. Let your work be your worship.",
        "Perform your work as an offering to the Divine. When your work is done to serve others rather than feed your own ego, it becomes a path to liberation and joy. This is the path of Karma Yoga.",
        "Do not be motivated by the fruits of your actions, nor be attached to inaction. Stand up, embrace your responsibilities, and perform them with dedication."
    ]
    
    advice_relationship = [
        "Seek to be a friend to all living beings, free from ego, possession, and attachment. True love is unconditional and acts without demanding anything in return. When you treat all beings with compassion, you see Me in everyone.",
        "The ego wants to control, while the soul wants to serve. When you experience friction with others, look inward at your own expectations. Let go of pride and communicate with gentleness.",
        "Remain balanced in both praise and insult, pleasure and pain. People's opinions are like winter and summer seasons—they come and go. Stand firm in your own inner peace."
    ]
    
    advice_default = [
        "Reflect deeply upon the teachings. Perform your duties with equanimity, rise above success and failure, and establish yourself in yoga. I am always with you, guiding your steps from within.",
        "Surrender all your doubts and fears to Me. When you take refuge in the divine wisdom, I shall deliver you from all anxieties. Do not fear, for you are eternally protected.",
        "Live a life of moderation, balance, and devotion. When your mind is connected to the Higher Self, the challenges of Kurukshetra will feel like mere ripples on the ocean."
    ]
    
    # Select variation based on keywords
    if any(w in q_lower for w in ["anxiety", "worry", "stress", "fear", "future", "nervous"]):
        intro = random.choice(intro_anxiety)
        advice = random.choice(advice_anxiety)
    elif any(w in q_lower for w in ["death", "loss", "grief", "sadness", "passed", "gone", "died"]):
        intro = random.choice(intro_death)
        advice = random.choice(advice_death)
    elif any(w in q_lower for w in ["anger", "angry", "frustrated", "control", "temper"]):
        intro = random.choice(intro_anger)
        advice = random.choice(advice_anger)
    elif any(w in q_lower for w in ["purpose", "meaning", "goal", "career"]):
        intro = random.choice(intro_purpose)
        advice = random.choice(advice_purpose)
    elif any(w in q_lower for w in ["relationship", "love", "friend", "family", "ego"]):
        intro = random.choice(intro_relationship)
        advice = random.choice(advice_relationship)
    else:
        intro = random.choice(intro_default)
        advice = random.choice(advice_default)
        
    # Resolve translation, fallback to Hindi if English translation is blank
    translation = primary_meta.get('translation_english')
    if not translation or len(translation.strip()) == 0:
        translation = f"{primary_meta.get('translation_hindi', '')} (Hindi Translation)"
        
    # Commentary fallback
    comm = primary_meta.get('commentary_hindi') or primary_meta.get('summary_hindi') or ""
    comm_section = f"\n\n**🔍 Deeper Commentary:**\n*{comm}*" if comm else ""

    response = f"""🌟 **My Dear Friend,**
    
{intro}

In Chapter {primary_meta.get('chapter', 2)}, Verse {primary_meta.get('verse', 47)} of the holy Gita, I spoke of this very truth:

> **📖 Chapter {primary_meta.get('chapter', 2)}, Verse {primary_meta.get('verse', 47)}**
> 
> *"{primary_meta.get('sanskrit', '')}"*
> 
> **Translation:** {translation}

---

### 💫 Krishna's Guidance:
{advice}{comm_section}

**🌱 Practical Steps to Practice:**
- **Surrender Attachment**: Focus on your effort, not the output. You cannot control what happens next, only how you act now.
- **Still the Mind**: Take 3 deep breaths when overwhelmed. Return to your breath and remember your divine nature.

🕉️ *I am always with you. Feel free to seek my guidance whenever your heart is heavy.*"""

    return response

# Main Chat Loop
if prompt := st.chat_input("What is troubling your soul today?"):
    # Render user query
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=seeker_avatar):
        st.markdown(prompt)
        
    # Generate response
    with st.chat_message("assistant", avatar=krishna_avatar):
        with st.spinner("📖 Krishna is reflecting on your words..."):
            
            # 1. Retrieve verses via vector RAG
            retrieved_verses = []
            if vector_store is not None:
                try:
                    search_results = vector_store.search(prompt, n_results=3)
                    if search_results and 'metadatas' in search_results and len(search_results['metadatas']) > 0:
                        retrieved_verses = search_results['metadatas'][0]
                except Exception as e:
                    st.sidebar.error(f"RAG search error: {e}")
            
            # Fallback to local hardcoded verses if RAG is empty
            if not retrieved_verses:
                retrieved_verses = fallback_static_verses
                
            # Render expander for references
            with st.expander("📖 View Referenced Verses from Bhagavad Gita"):
                for idx, v in enumerate(retrieved_verses, 1):
                    ch = v.get('chapter', 0)
                    v_num = v.get('verse', 0)
                    ch_eng = v.get('chapter_name_english', 'Introduction')
                    st.markdown(f"**{idx}. Chapter {ch} ({ch_eng}), Verse {v_num}**")
                    if v.get('sanskrit'):
                        st.markdown(f"`{v.get('sanskrit')}`")
                        
                    # Handle translation rendering
                    trans = v.get('translation_english')
                    if not trans or len(trans.strip()) == 0:
                        trans = f"{v.get('translation_hindi', '')} (Hindi Translation)"
                    st.markdown(f"**Translation:** {trans}")
                    
                    if v.get('commentary_hindi'):
                        st.markdown(f"**Commentary:** {v.get('commentary_hindi')}")
                    if idx < len(retrieved_verses):
                        st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
            
            # 2. Generate response (Gemini LLM vs. Fallback Template)
            if gemini_key:
                response = generate_llm_guidance(prompt, retrieved_verses, gemini_key)
            else:
                response = generate_offline_guidance(prompt, retrieved_verses)
                
            # Render response
            st.markdown(response)
            
            # 3. Text-to-Speech audio generation
            audio_bytes = None
            if enable_audio:
                audio_bytes = generate_speech_audio(response)
                if audio_bytes is not None:
                    st.audio(audio_bytes, format="audio/mp3")
            
            # Save message and audio
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "audio": audio_bytes
            })