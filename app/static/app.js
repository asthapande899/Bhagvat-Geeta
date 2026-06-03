// app/static/app.js

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    // DOM Elements
    const providerSelect = document.getElementById('provider-select');
    const apiKeyContainer = document.getElementById('api-key-container');
    const apiKeyInput = document.getElementById('api-key-input');
    const voiceToggle = document.getElementById('voice-toggle');
    const bgFlute = document.getElementById('bg-flute');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    // API Help boxes
    const helpBoxes = {
        gemini: document.getElementById('gemini-help'),
        groq: document.getElementById('groq-help'),
        openai: document.getElementById('openai-help')
    };

    // Tracks currently playing TTS audio so we can pause it
    let currentTtsAudio = null;
    let currentTtsButton = null;

    // Welcome Message on load
    addMessageBubble(
        "🙏 Welcome, seeker of truth. I am here to share the timeless path of the Bhagavad Gita with you. Tell me, what challenges or questions are troubling your mind on your life's battlefield today?",
        "assistant"
    );

    // Toggle API Key input visibility based on provider selection
    if (providerSelect) {
        providerSelect.addEventListener('change', () => {
            const val = providerSelect.value;
            if (val === 'offline') {
                if (apiKeyContainer) apiKeyContainer.style.display = 'none';
            } else {
                if (apiKeyContainer) apiKeyContainer.style.display = 'flex';
                // Show help box for selected provider and hide others
                Object.keys(helpBoxes).forEach(key => {
                    if (helpBoxes[key]) {
                        if (key === val) {
                            helpBoxes[key].style.display = 'block';
                        } else {
                            helpBoxes[key].style.display = 'none';
                        }
                    }
                });
            }
        });
    }

    // Form Submit (User sends message)
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add User Message bubble
        addMessageBubble(message, 'user');
        chatInput.value = '';
        
        // Show Typing Spinner
        const spinnerId = showTypingSpinner();
        
        // Prep payload
        const payload = {
            message: message,
            provider: providerSelect ? providerSelect.value : 'groq',
            api_key: apiKeyInput ? apiKeyInput.value.trim() : '',
            enable_voice: voiceToggle.checked
        };
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            // Remove spinner
            removeTypingSpinner(spinnerId);
            
            if (response.ok) {
                // Add Assistant Message bubble
                addMessageBubble(data.response, 'assistant', data.audio, data.verses);
            } else {
                addMessageBubble(`⚠️ Error: ${data.error || 'Unable to connect to Krishna\'s wisdom.'}`, 'assistant');
            }
        } catch (err) {
            removeTypingSpinner(spinnerId);
            addMessageBubble(`⚠️ Failed to connect to server: ${err.message}`, 'assistant');
        }
    });

    // Create and insert message bubble
    function addMessageBubble(text, role, audioBase64 = null, verses = []) {
        const row = document.createElement('div');
        row.classList.add('message-row', `${role}-row`);
        
        // Avatar
        const avatarContainer = document.createElement('div');
        avatarContainer.classList.add('avatar-container');
        
        const avatarImg = document.createElement('img');
        if (role === 'assistant') {
            avatarImg.src = '/assets/krishna_avatar.png';
            avatarImg.alt = 'Krishna';
        } else {
            avatarImg.src = '/assets/seeker_avatar.png';
            avatarImg.alt = 'Seeker';
        }
        
        // Fallback for avatar image errors
        avatarImg.onerror = () => {
            avatarContainer.innerHTML = `<span class="avatar-placeholder">${role === 'assistant' ? '🕉️' : '👤'}</span>`;
        };
        avatarContainer.appendChild(avatarImg);
        
        // Speech Bubble
        const bubble = document.createElement('div');
        bubble.classList.add('bubble-content');
        
        // Parse markdown formatting inside text
        bubble.innerHTML = parseMarkdown(text);
        
        // Render Voice Player if audio is provided (base64 string)
        if (role === 'assistant' && audioBase64) {
            const audioDiv = document.createElement('div');
            audioDiv.classList.add('bubble-audio-player');
            
            const playBtn = document.createElement('button');
            playBtn.classList.add('audio-play-btn');
            playBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
            
            const statusText = document.createElement('span');
            statusText.classList.add('audio-status-text');
            statusText.textContent = "Listen to Krishna's voice";
            
            // Audio playback controller
            const audio = new Audio("data:audio/mp3;base64," + audioBase64);
            
            playBtn.addEventListener('click', () => {
                if (currentTtsAudio && currentTtsAudio !== audio) {
                    currentTtsAudio.pause();
                    if (currentTtsButton) {
                        currentTtsButton.innerHTML = '<i class="fa-solid fa-play"></i>';
                        currentTtsButton.nextElementSibling.textContent = "Listen to Krishna's voice";
                    }
                }
                
                if (audio.paused) {
                    audio.play();
                    playBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
                    statusText.textContent = "Speaking guidance...";
                    currentTtsAudio = audio;
                    currentTtsButton = playBtn;
                } else {
                    audio.pause();
                    playBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
                    statusText.textContent = "Listen to Krishna's voice";
                }
            });
            
            audio.addEventListener('ended', () => {
                playBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
                statusText.textContent = "Listen to Krishna's voice";
                if (currentTtsAudio === audio) {
                    currentTtsAudio = null;
                    currentTtsButton = null;
                }
            });
            
            audioDiv.appendChild(playBtn);
            audioDiv.appendChild(statusText);
            bubble.appendChild(audioDiv);
            
            // Proactively auto-play latest message if voice is toggled on
            if (voiceToggle.checked) {
                setTimeout(() => {
                    playBtn.click();
                }, 500);
            }
        }
        
        // Render referenced verses in accordion expander
        if (role === 'assistant' && verses && verses.length > 0) {
            const expander = document.createElement('div');
            expander.classList.add('verse-expander');
            
            const header = document.createElement('div');
            header.classList.add('verse-expander-header');
            header.innerHTML = '<span>📖 View Referenced Verses</span> <i class="fa-solid fa-chevron-down"></i>';
            
            const body = document.createElement('div');
            body.classList.add('verse-expander-body');
            
            verses.forEach((v, idx) => {
                const verseBlock = document.createElement('div');
                verseBlock.classList.add('referenced-verse-block');
                
                let sanskritHtml = v.sanskrit ? `<div class="verse-sanskrit">${v.sanskrit}</div>` : '';
                let commHtml = v.commentary ? `<div class="verse-translation" style="margin-top:5px; font-style:italic; color:#94a3b8;"><b>Commentary:</b> ${v.commentary}</div>` : '';
                
                verseBlock.innerHTML = `
                    <div class="verse-title">${idx + 1}. Chapter ${v.chapter} (${v.chapter_name_english}), Verse ${v.verse}</div>
                    ${sanskritHtml}
                    <div class="verse-translation"><b>Translation:</b> ${v.translation}</div>
                    ${commHtml}
                    ${idx < verses.length - 1 ? '<div class="gold-divider" style="margin: 10px 0;"></div>' : ''}
                `;
                body.appendChild(verseBlock);
            });
            
            header.addEventListener('click', () => {
                expander.classList.toggle('open');
            });
            
            expander.appendChild(header);
            expander.appendChild(body);
            bubble.appendChild(expander);
        }
        
        row.appendChild(avatarContainer);
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        
        // Scroll dynamically: for assistant responses, align to the start of the response so the user can read from the beginning
        if (role === 'assistant') {
            row.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Typing spinner logic
    function showTypingSpinner() {
        const id = 'spinner_' + Date.now();
        const row = document.createElement('div');
        row.classList.add('message-row', 'assistant-row');
        row.id = id;
        
        const avatarContainer = document.createElement('div');
        avatarContainer.classList.add('avatar-container');
        const avatarImg = document.createElement('img');
        avatarImg.src = '/assets/krishna_avatar.png';
        avatarImg.onerror = () => {
            avatarContainer.innerHTML = '<span class="avatar-placeholder">🕉️</span>';
        };
        avatarContainer.appendChild(avatarImg);
        
        const bubble = document.createElement('div');
        bubble.classList.add('bubble-content');
        bubble.innerHTML = `
            <div class="typing-spinner">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        
        row.appendChild(avatarContainer);
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeTypingSpinner(id) {
        const spinner = document.getElementById(id);
        if (spinner) spinner.remove();
    }

    // Markdown Parser Helper
    function parseMarkdown(text) {
        // Safe characters escaping
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Format headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Format blockquotes (lines starting with > or &gt;)
        html = html.replace(/^\s*&gt;\s+(.*$)/gim, '<blockquote><p>$1</p></blockquote>');
        // Merge contiguous blockquotes
        html = html.replace(/<\/blockquote>\s*<blockquote>/g, '<br>');

        // Bold text **bold**
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Italic text *italic*
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Single lines list formatting
        html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');

        // Format dividers (---)
        html = html.replace(/^---$/gim, '<hr>');

        // Map standard newlines to breaktags
        html = html.replace(/\n/g, '<br>');

        return html;
    }
});
