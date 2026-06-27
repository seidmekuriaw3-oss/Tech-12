// ==================== SEMIRA AI AGENT ====================
(function () {
    'use strict';

    const AI_ENDPOINT = '/api/ai-chat';
    const SUGGESTIONS_ENDPOINT = '/api/ai-chat/suggestions';
    const MAX_HISTORY = 16;

    let history = [];
    let isOpen = false;
    let isTyping = false;
    let suggestions = [];

    // ---- DOM references (set after DOMContentLoaded) ----
    let panel, msgList, inputEl, sendBtn, badge, toggleBtn;

    // ---- Init ----
    function init() {
        panel     = document.getElementById('semira-ai-panel');
        msgList   = document.getElementById('semira-ai-messages');
        inputEl   = document.getElementById('semira-ai-input');
        sendBtn   = document.getElementById('semira-ai-send');
        badge     = document.getElementById('semira-ai-badge');
        toggleBtn = document.getElementById('semira-ai-toggle');

        if (!panel) return;

        sendBtn.addEventListener('click', handleSend);
        inputEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
        });
        inputEl.addEventListener('input', function () {
            sendBtn.disabled = !this.value.trim();
        });

        // Load suggestions
        fetch(SUGGESTIONS_ENDPOINT)
            .then(r => r.json())
            .then(d => { if (d.success) suggestions = d.suggestions; })
            .catch(() => {});

        // Show badge pulse after 3s
        setTimeout(function () {
            if (!isOpen && badge) {
                badge.style.display = 'flex';
                badge.classList.add('ai-badge-pulse');
            }
        }, 3000);
    }

    // ---- Toggle panel ----
    window.toggleAIPanel = function () {
        isOpen = !isOpen;
        if (isOpen) {
            panel.classList.add('open');
            if (badge) badge.style.display = 'none';
            if (msgList.children.length === 0) showWelcome();
            setTimeout(() => inputEl && inputEl.focus(), 300);
        } else {
            panel.classList.remove('open');
        }
    };

    window.closeAIPanel = function () {
        isOpen = false;
        panel.classList.remove('open');
    };

    // ---- Welcome message ----
    function showWelcome() {
        const lang = document.documentElement.lang || 'am';
        let welcome;
        if (lang === 'ar') {
            welcome = 'أهلاً! 👗 أنا سيميرا، مساعدك في SEMIRA FASHION. كيف يمكنني مساعدتك اليوم؟';
        } else if (lang === 'en') {
            welcome = "Hello! 👗 I'm SEMIRA, your AI shopping assistant. How can I help you today?";
        } else {
            welcome = 'ሰላም! 👗 እኔ ሰሚራ ነኝ — የ SEMIRA FASHION AI አስተናጋጅ። ምን ልርዳዎ?';
        }
        appendMessage('assistant', welcome);
        if (suggestions.length) setTimeout(showSuggestions, 400);
    }

    // ---- Suggestion chips ----
    function showSuggestions() {
        if (!msgList) return;
        const div = document.createElement('div');
        div.className = 'ai-suggestions';
        div.id = 'ai-suggestion-chips';
        suggestions.forEach(function (s) {
            const btn = document.createElement('button');
            btn.className = 'ai-chip';
            btn.textContent = s;
            btn.onclick = function () {
                div.remove();
                inputEl.value = s;
                handleSend();
            };
            div.appendChild(btn);
        });
        msgList.appendChild(div);
        scrollBottom();
    }

    // ---- Send handler ----
    function handleSend() {
        const text = inputEl ? inputEl.value.trim() : '';
        if (!text || isTyping) return;
        inputEl.value = '';
        sendBtn.disabled = true;

        // Remove suggestion chips if still visible
        const chips = document.getElementById('ai-suggestion-chips');
        if (chips) chips.remove();

        appendMessage('user', text);
        showTyping();

        const payload = { message: text, history: history.slice(-MAX_HISTORY) };

        fetch(AI_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            hideTyping();
            const reply = d.reply || 'ይቅርታ፣ አሁን ልረዳ አልቻልኩም። እንደገና ይሞክሩ።';
            appendMessage('assistant', reply);
            history.push({ role: 'user', content: text });
            history.push({ role: 'assistant', content: reply });
            if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
        })
        .catch(function () {
            hideTyping();
            appendMessage('assistant', 'ይቅርታ፣ ግንኙነት ችግር ነበር። እንደገና ይሞክሩ።');
        });
    }

    // ---- Append message bubble ----
    function appendMessage(role, content) {
        if (!msgList) return;
        const wrap = document.createElement('div');
        wrap.className = 'ai-msg-wrap ai-msg-' + role;

        const bubble = document.createElement('div');
        bubble.className = 'ai-bubble';
        // Allow links in assistant messages
        if (role === 'assistant') {
            bubble.innerHTML = linkify(escapeHtml(content));
        } else {
            bubble.textContent = content;
        }
        wrap.appendChild(bubble);
        msgList.appendChild(wrap);
        scrollBottom();

        // Animate in
        requestAnimationFrame(function () { wrap.classList.add('ai-msg-visible'); });
    }

    // ---- Typing indicator ----
    function showTyping() {
        isTyping = true;
        if (!msgList) return;
        const div = document.createElement('div');
        div.className = 'ai-msg-wrap ai-msg-assistant';
        div.id = 'ai-typing-indicator';
        div.innerHTML = '<div class="ai-bubble ai-typing"><span></span><span></span><span></span></div>';
        msgList.appendChild(div);
        scrollBottom();
        requestAnimationFrame(function () { div.classList.add('ai-msg-visible'); });
    }

    function hideTyping() {
        isTyping = false;
        const el = document.getElementById('ai-typing-indicator');
        if (el) el.remove();
    }

    // ---- Helpers ----
    function scrollBottom() {
        if (msgList) msgList.scrollTop = msgList.scrollHeight;
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function linkify(str) {
        // Convert escaped &lt;a href...&gt; back to links
        str = str.replace(/&lt;a href='([^']+)'([^&]*)&gt;([^&]*)&lt;\/a&gt;/g,
            '<a href="$1" $2 target="_blank" rel="noopener">$3</a>');
        // Convert plain URLs to links
        str = str.replace(/(https?:\/\/[^\s<]+)/g,
            '<a href="$1" target="_blank" rel="noopener">$1</a>');
        // WhatsApp shorthand
        str = str.replace(/wa\.me\/(\d+)/g,
            '<a href="https://wa.me/$1" target="_blank" rel="noopener" style="color:#25d366;font-weight:600">📱 WhatsApp</a>');
        // Convert /products links
        str = str.replace(/href='\/([^']+)'/g, 'href="/$1"');
        // Newlines to <br>
        str = str.replace(/\n/g, '<br>');
        return str;
    }

    // ---- Boot ----
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
