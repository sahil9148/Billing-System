/* ============================================
   BillFlow Pro — Chatbot Widget
   ============================================ */
const Chatbot = {
    isOpen: false,

    init() {
        document.getElementById('chatbot-toggle').addEventListener('click', () => this.toggle());
        document.getElementById('chatbot-close').addEventListener('click', () => this.close());
        document.getElementById('chat-send').addEventListener('click', () => this.send());
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.send();
        });

        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const msg = chip.dataset.message;
                document.getElementById('chat-input').value = msg;
                this.send();
            });
        });
    },

    toggle() {
        this.isOpen ? this.close() : this.open();
    },

    open() {
        this.isOpen = true;
        document.getElementById('chatbot-window').classList.remove('hidden');
        document.querySelector('.chat-icon').classList.add('hidden');
        document.querySelector('.chat-close').classList.remove('hidden');
        document.getElementById('chatbot-toggle').style.animation = 'none';
        document.getElementById('chat-input').focus();
    },

    close() {
        this.isOpen = false;
        document.getElementById('chatbot-window').classList.add('hidden');
        document.querySelector('.chat-icon').classList.remove('hidden');
        document.querySelector('.chat-close').classList.add('hidden');
        document.getElementById('chatbot-toggle').style.animation = 'pulse 3s ease-in-out infinite';
    },

    addMessage(text, type) {
        const container = document.getElementById('chatbot-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${type}`;
        msgDiv.innerHTML = `<div class="message-bubble">${escapeHTML(text)}</div>`;
        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
    },

    showTyping() {
        const container = document.getElementById('chatbot-messages');
        const typing = document.createElement('div');
        typing.className = 'chat-message bot';
        typing.id = 'typing-indicator';
        typing.innerHTML = `<div class="message-bubble typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>`;
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    },

    hideTyping() {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    },

    async send() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;

        input.value = '';
        this.addMessage(message, 'user');
        this.showTyping();

        try {
            const data = await API.post('/api/chat', { message });
            this.hideTyping();
            if (data && data.response) {
                const container = document.getElementById('chatbot-messages');
                const msgDiv = document.createElement('div');
                msgDiv.className = 'chat-message bot';
                msgDiv.innerHTML = `<div class="message-bubble">${data.response.replace(/\n/g, '<br>')}</div>`;
                container.appendChild(msgDiv);
                container.scrollTop = container.scrollHeight;
            }
        } catch (err) {
            this.hideTyping();
            const container = document.getElementById('chatbot-messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'chat-message bot';
            msgDiv.innerHTML = `<div class="message-bubble">Sorry, I encountered an error. Please try again.</div>`;
            container.appendChild(msgDiv);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => Chatbot.init());
