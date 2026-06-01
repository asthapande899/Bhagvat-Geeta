# app/simple_chatbot.py
import streamlit as st
import random

# Bhagavad Gita verses database
verses = [
    {
        "chapter": 2,
        "verse": 47,
        "text": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
        "tags": ["duty", "action", "attachment", "work", "karma"]
    },
    {
        "chapter": 2,
        "verse": 14,
        "text": "O son of Kunti, the nonpermanent appearance of happiness and distress, and their disappearance in due course, are like the appearance and disappearance of winter and summer seasons. They arise from sense perception, and one must learn to tolerate them without being disturbed.",
        "tags": ["happiness", "sadness", "patience", "emotions", "anxiety"]
    },
    {
        "chapter": 2,
        "verse": 22,
        "text": "As a person puts on new garments, giving up old ones, the soul similarly accepts new material bodies, giving up the old and useless ones.",
        "tags": ["death", "soul", "reincarnation", "loss", "fear"]
    },
    {
        "chapter": 6,
        "verse": 5,
        "text": "One must elevate oneself by one's own mind, not degrade oneself. The mind is the friend of the conditioned soul, and his enemy as well.",
        "tags": ["self-help", "mindset", "motivation", "inner-strength"]
    },
    {
        "chapter": 3,
        "verse": 19,
        "text": "Therefore, without being attached to the fruits of activities, one should act as a matter of duty, for by working without attachment, one attains the Supreme.",
        "tags": ["detachment", "duty", "success", "work-life"]
    },
    {
        "chapter": 2,
        "verse": 27,
        "text": "For one who has taken birth, death is certain; and for one who is dead, birth is certain. Therefore, in an unavoidable situation, you should not lament.",
        "tags": ["death", "grief", "acceptance", "loss", "sadness"]
    },
    {
        "chapter": 4,
        "verse": 7,
        "text": "Whenever and wherever there is a decline in righteousness and a rise in unrighteousness, O descendent of Bharata, at that time I manifest Myself.",
        "tags": ["purpose", "divine", "righteousness", "faith"]
    },
    {
        "chapter": 6,
        "verse": 35,
        "text": "O mighty-armed son of Kunti, it is undoubtedly very difficult to curb the restless mind, but it is possible by constant practice and detachment.",
        "tags": ["mind-control", "discipline", "meditation", "focus", "calm"]
    },
    {
        "chapter": 12,
        "verse": 13,
        "text": "One who is not envious but is a kind friend to all living entities, who does not think himself a proprietor and is free from false ego, who is equal in both happiness and distress, who is tolerant.",
        "tags": ["friendship", "kindness", "ego", "relationships", "compassion"]
    },
    {
        "chapter": 18,
        "verse": 66,
        "text": "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions. Do not fear.",
        "tags": ["surrender", "faith", "peace", "fear", "hope"]
    },
    {
        "chapter": 2,
        "verse": 62,
        "text": "Perform your duty equipoised, O Arjuna, abandoning all attachment to success or failure. Such equanimity is called yoga.",
        "tags": ["balance", "yoga", "success", "failure", "mindset"]
    },
    {
        "chapter": 16,
        "verse": 21,
        "text": "There are three gates leading to this hell — lust, anger, and greed. Every sane man should give these up, for they lead to the degradation of the soul.",
        "tags": ["anger", "greed", "lust", "self-control", "discipline"]
    },
    {
        "chapter": 2,
        "verse": 47,
        "text": "You have control over action alone, never over its fruits. Live not for the fruits of action, nor attach yourself to inaction.",
        "tags": ["action", "detachment", "mindfulness", "focus"]
    }
]

def find_relevant_verses(question):
    """Find verses relevant to the user's question"""
    question_lower = question.lower()
    scored_verses = []
    
    # Keywords for different topics
    topic_keywords = {
        "anxiety": ["anxiety", "worry", "stress", "nervous", "fear", "tension", "scared"],
        "death": ["death", "die", "loss", "passed", "gone", "dead", "dying"],
        "anger": ["anger", "angry", "frustrated", "rage", "mad", "frustration"],
        "work": ["work", "career", "job", "duty", "responsibility", "profession"],
        "relationship": ["relationship", "friend", "love", "partner", "family", "people"],
        "purpose": ["purpose", "meaning", "goal", "aim", "direction", "destiny"],
        "happiness": ["happy", "happiness", "joy", "pleasure", "bliss"],
        "sadness": ["sad", "depressed", "lonely", "unhappy", "grief"],
        "peace": ["peace", "calm", "tranquil", "quiet", "mindful"],
        "success": ["success", "fail", "failure", "achieve", "accomplish"]
    }
    
    for verse in verses:
        score = 0
        verse_text = verse['text'].lower()
        
        # Score based on tags matching
        for tag in verse['tags']:
            if tag in question_lower:
                score += 3
        
        # Score based on topic keywords
        for topic, keywords in topic_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                for tag in verse['tags']:
                    if topic in tag or tag in topic:
                        score += 2
        
        # Score based on direct word matches
        words = question_lower.split()
        for word in words:
            if len(word) > 3 and word in verse_text:
                score += 1
        
        scored_verses.append((score, verse))
    
    # Sort by score and return top 3
    scored_verses.sort(reverse=True, key=lambda x: x[0])
    top_verses = [verse for score, verse in scored_verses[:3] if score > 0]
    
    # Return default if no matches
    return top_verses if top_verses else [verses[0]]

def generate_response(question, verses_found):
    """Generate a thoughtful response"""
    primary_verse = verses_found[0]
    question_lower = question.lower()
    
    # Start with the verse
    response = f"""**📖 Chapter {primary_verse['chapter']}, Verse {primary_verse['verse']}**

*"{primary_verse['text']}"*

---

"""
    
    # Add personalized guidance based on question type
    if any(word in question_lower for word in ["anxiety", "worry", "stress", "nervous"]):
        response += """**💫 Understanding Your Anxiety:**

Krishna teaches that anxiety comes from attaching ourselves to outcomes. When we worry about results, we lose peace in the present moment.

**🌱 Practical Wisdom:**
• Focus on your actions, not the results
• Take one step at a time - the present moment is all you have
• Trust that you have the strength to handle whatever comes
• Remember: This too shall pass

"""
    elif any(word in question_lower for word in ["death", "loss", "passed", "gone", "died"]):
        response += """**💫 Finding Peace in Loss:**

The Gita reveals that the soul is eternal. Your loved one's journey continues, though their physical form has changed. Grief is natural, but know that love transcends physical presence.

**🌱 Finding Comfort:**
• Cherish the memories and lessons they gave you
• Their soul continues its eternal journey
• Your love for them remains forever
• In time, grief transforms into gratitude

"""
    elif any(word in question_lower for word in ["anger", "angry", "frustrated", "frustration"]):
        response += """**💫 Transforming Anger:**

Anger clouds our judgment and leads to actions we regret. Krishna advises us to develop tolerance and self-awareness.

**🌱 Working with Anger:**
• Pause before reacting - take 5 deep breaths
• Ask yourself: Will this matter tomorrow?
• Channel that energy into constructive action
• Practice forgiveness - for yourself and others

"""
    elif any(word in question_lower for word in ["purpose", "meaning", "career", "goal"]):
        response += """**💫 Discovering Your Purpose:**

Your purpose unfolds through conscious action. Krishna emphasizes doing your duty with awareness, without attachment to results.

**🌱 Finding Your Path:**
• What brings you joy AND serves others?
• Your unique talents are gifts meant to be shared
• Purpose is found in action, not just thinking
• Trust the journey - clarity comes through doing

"""
    elif any(word in question_lower for word in ["relationship", "friend", "love", "family"]):
        response += """**💫 Wisdom for Relationships:**

The Gita teaches us to be a kind friend to all beings, free from false ego, and balanced in both happiness and distress.

**🌱 Nurturing Relationships:**
• Give without expecting in return
• Practice compassion and understanding
• Let go of ego and the need to be right
• Be present and truly listen

"""
    else:
        response += """**💫 Applying This Wisdom:**

The verse above contains guidance for your situation. Take a moment to reflect on how it speaks to your heart.

**🌱 Reflection Questions:**
• How does this teaching apply to my current situation?
• What would change if I truly understood this?
• How can I practice this wisdom today?

"""
    
    # Add additional verses if available
    if len(verses_found) > 1:
        response += f"""**📚 Additional Wisdom:**
*Chapter {verses_found[1]['chapter']}, Verse {verses_found[1]['verse']}*
*"{verses_found[1]['text'][:150]}..."*

"""
    
    # Closing message
    closings = [
        "🕉️ *May this wisdom guide you. Feel free to ask more questions.*",
        "🌟 *Krishna's teachings are timeless. What else would you like to explore?*",
        "🙏 *Remember, the answers you seek are already within you. Keep asking, keep growing.*"
    ]
    response += random.choice(closings)
    
    return response

# Streamlit App Configuration
st.set_page_config(
    page_title="Bhagavad Gita AI Counselor",
    page_icon="🕉️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .st-emotion-cache-1c7y2kd {
        background-color: #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)

# Title and Description
st.title("🕉️ Bhagavad Gita Wisdom")
st.markdown("""
<div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 1.5rem; border-radius: 1rem; margin-bottom: 2rem;'>
<p style='font-size: 1.1rem; margin: 0; text-align: center;'>
<i>"When Arjuna was confused on the battlefield of life, Krishna answered his questions with eternal wisdom.<br>
Now, ask your questions and find guidance through the timeless teachings of the Bhagavad Gita."</i>
</p>
</div>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "🙏 Welcome, seeker of wisdom! I'm here to share the timeless teachings of the Bhagavad Gita. What's on your mind today? You can ask about:\n\n• Anxiety and stress\n• Purpose in life\n• Dealing with loss\n• Managing anger\n• Relationships\n• Finding peace\n\nOr anything else you're going through."}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What's troubling you? Ask anything about life..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("📖 Reflecting on Krishna's wisdom..."):
            # Find relevant verses
            relevant_verses = find_relevant_verses(prompt)
            
            # Show verses in expander
            with st.expander("📖 View Referenced Verses from Bhagavad Gita"):
                for i, verse in enumerate(relevant_verses, 1):
                    st.markdown(f"**{i}. Chapter {verse['chapter']}, Verse {verse['verse']}**")
                    st.markdown(f"*{verse['text']}*")
                    st.markdown(f"🏷️ Tags: {', '.join(verse['tags'])}")
                    if i < len(relevant_verses):
                        st.markdown("---")
            
            # Generate and display response
            response = generate_response(prompt, relevant_verses)
            st.markdown(response)
    
    # Add assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with information
with st.sidebar:
    st.markdown("## 🕉️ About This App")
    st.markdown("""
    This AI counselor shares wisdom from the **Bhagavad Gita** — a 700-verse scripture 
    containing Krishna's teachings to Arjuna on life, duty, and self-realization.
    
    ### How it works:
    1. Ask any question about life
    2. The system finds relevant verses
    3. You receive guidance with practical wisdom
    
    ### Try asking about:
    • "I'm feeling anxious about my future"
    • "How do I deal with loss?"
    • "What is my purpose?"
    • "I'm struggling with anger"
    • "How can I find peace?"
    
    ### 📖 Key Teachings:
    - **Karma Yoga:** Act without attachment to results
    - **Jnana Yoga:** Wisdom and self-knowledge
    - **Bhakti Yoga:** Devotion and surrender
    - **Dhyana Yoga:** Meditation and self-control
    """)
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center;'>
    <small>Made with 🙏 using AI & Gita's eternal wisdom</small>
    </div>
    """, unsafe_allow_html=True)

print("✅ App loaded successfully!")