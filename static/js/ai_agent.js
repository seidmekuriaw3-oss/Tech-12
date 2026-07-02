// ==================== SEMIRA AI AGENT ====================
(function () {
    'use strict';

    var AI_ENDPOINT = '/api/ai-chat';
    var SUGGESTIONS_ENDPOINT = '/api/ai-chat/suggestions';
    var MAX_HISTORY = 16;
    var SESSION_KEY = 'semira_ai_history';

    var history = [];
    var isOpen = false;
    var isTyping = false;
    var suggestions = [];

    var panel, msgList, inputEl, sendBtn, badge, toggleBtn;

    // ── Load/save history via sessionStorage ──────────────────────────────
    function loadHistory() {
        try {
            var raw = sessionStorage.getItem(SESSION_KEY);
            if (raw) history = JSON.parse(raw);
        } catch (e) { history = []; }
    }

    function saveHistory() {
        try {
            sessionStorage.setItem(SESSION_KEY, JSON.stringify(history.slice(-MAX_HISTORY)));
        } catch (e) {}
    }

    // ── Init ──────────────────────────────────────────────────────────────
    function init() {
        panel     = document.getElementById('semira-ai-panel');
        msgList   = document.getElementById('semira-ai-messages');
        inputEl   = document.getElementById('semira-ai-input');
        sendBtn   = document.getElementById('semira-ai-send');
        badge     = document.getElementById('semira-ai-badge');
        toggleBtn = document.getElementById('semira-ai-toggle');

        if (!panel) return;

        loadHistory();

        sendBtn.addEventListener('click', handleSend);
        inputEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
        });
        inputEl.addEventListener('input', function () {
            sendBtn.disabled = !this.value.trim();
            // Auto-resize textarea
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });

        fetch(SUGGESTIONS_ENDPOINT)
            .then(function (r) { return r.json(); })
            .then(function (d) { if (d.success) suggestions = d.suggestions; })
            .catch(function () {});

        // Pulse badge after 4s if user hasn't opened
        setTimeout(function () {
            if (!isOpen && badge) {
                badge.style.display = 'flex';
                badge.classList.add('ai-badge-pulse');
            }
        }, 4000);
    }

    // ── Toggle / Close ────────────────────────────────────────────────────
    window.toggleAIPanel = function () {
        isOpen = !isOpen;
        if (isOpen) {
            panel.classList.add('open');
            if (badge) { badge.style.display = 'none'; badge.classList.remove('ai-badge-pulse'); }
            if (msgList.children.length === 0) {
                if (history.length > 0) {
                    restoreHistory();
                } else {
                    showWelcome();
                }
            }
            setTimeout(function () { if (inputEl) inputEl.focus(); }, 300);
        } else {
            panel.classList.remove('open');
        }
    };

    window.closeAIPanel = function () {
        isOpen = false;
        panel.classList.remove('open');
    };

    window.clearAIChat = function () {
        history = [];
        saveHistory();
        if (msgList) {
            msgList.innerHTML = '';
            showWelcome();
        }
    };

    // ── Restore history from sessionStorage ───────────────────────────────
    function restoreHistory() {
        history.forEach(function (h) {
            if (h.role === 'user' || h.role === 'assistant') {
                appendMessage(h.role, h.content, true);
            }
        });
        scrollBottom();
    }

    // ── Welcome message ───────────────────────────────────────────────────
    function showWelcome() {
        var lang = document.documentElement.lang || 'am';
        var welcome = {
            ar: 'أهلاً! 👗 أنا سيميرا، مساعدك في SEMIRA FASHION. كيف يمكنني مساعدتك اليوم؟',
            en: "Hello! 👗 I'm SEMIRA, your AI shopping assistant. How can I help you today?",
            am: 'ሰላም! 👗 እኔ ሰሚራ ነኝ — የ SEMIRA FASHION AI አስተናጋጅ። ምን ልርዳዎ?',
        }[lang] || 'ሰላም! 👗 እኔ ሰሚራ ነኝ — የ SEMIRA FASHION AI አስተናጋጅ። ምን ልርዳዎ?';
        appendMessage('assistant', welcome, true);
        if (suggestions.length) setTimeout(showSuggestions, 400);
    }

    // ── Suggestion chips ──────────────────────────────────────────────────
    function showSuggestions() {
        if (!msgList) return;
        var div = document.createElement('div');
        div.className = 'ai-suggestions';
        div.id = 'ai-suggestion-chips';
        suggestions.forEach(function (s) {
            var btn = document.createElement('button');
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

    // ── Send handler ──────────────────────────────────────────────────────
    function handleSend() {
        var text = inputEl ? inputEl.value.trim() : '';
        if (!text || isTyping) return;
        inputEl.value = '';
        inputEl.style.height = 'auto';
        sendBtn.disabled = true;

        var chips = document.getElementById('ai-suggestion-chips');
        if (chips) chips.remove();

        appendMessage('user', text, true);
        showTyping();

        fetch(AI_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: history.slice(-MAX_HISTORY) })
        })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (d) {
            hideTyping();
            var reply = d.reply || 'ይቅርታ፣ አሁን ልረዳ አልቻልኩም። እንደገና ይሞክሩ።';
            appendMessage('assistant', reply, true);
            history.push({ role: 'user', content: text });
            history.push({ role: 'assistant', content: reply });
            if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
            saveHistory();
        })
        .catch(function (err) {
            hideTyping();
            var lang = document.documentElement.lang || 'am';
            var errMsg = {
                ar: 'عذراً، حدث خطأ في الاتصال. حاول مرة أخرى.',
                en: 'Sorry, a connection error occurred. Please try again.',
                am: 'ይቅርታ፣ ግንኙነት ችግር ነበር። እንደገና ይሞክሩ።',
            }[lang] || 'ይቅርታ፣ ግንኙነት ችግር ነበር። እንደገና ይሞክሩ።';
            appendMessage('assistant', errMsg, true);
            console.warn('AI Agent error:', err);
        });
    }

    // ── Message bubble ────────────────────────────────────────────────────
    function appendMessage(role, content, animate) {
        if (!msgList) return;
        var wrap = document.createElement('div');
        wrap.className = 'ai-msg-wrap ai-msg-' + role;

        var bubble = document.createElement('div');
        bubble.className = 'ai-bubble';

        if (role === 'assistant') {
            // Safe rendering: escape first, then allow whitelisted HTML
            bubble.innerHTML = safeRender(content);
        } else {
            bubble.textContent = content;
        }

        wrap.appendChild(bubble);
        msgList.appendChild(wrap);
        scrollBottom();

        if (animate !== false) {
            requestAnimationFrame(function () { wrap.classList.add('ai-msg-visible'); });
        } else {
            wrap.classList.add('ai-msg-visible');
        }
    }

    // ── Safe HTML renderer (replaces linkify — no XSS) ───────────────────
    function safeRender(text) {
        // 1. Escape all HTML entities
        var escaped = String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

        // 2. Convert newlines to <br>
        escaped = escaped.replace(/\n/g, '<br>');

        // 3. Convert plain https:// URLs to safe links
        escaped = escaped.replace(
            /(https?:\/\/[^\s<&"']+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );

        // 4. Convert wa.me/number shorthand
        escaped = escaped.replace(
            /wa\.me\/(\d+)/g,
            '<a href="https://wa.me/$1" target="_blank" rel="noopener noreferrer" style="color:#25d366;font-weight:600">📱 WhatsApp</a>'
        );

        // 5. Convert safe internal links like /orders /products
        escaped = escaped.replace(
            /\/(orders|products|categories|cart|profile|login|register|about|contact|search|wishlist)((?:\/[a-zA-Z0-9_-]+)*)/g,
            '<a href="/$1$2" style="color:#1a7a4a;font-weight:600">/$1$2 →</a>'
        );

        return escaped;
    }

    // ── Typing indicator ──────────────────────────────────────────────────
    function showTyping() {
        isTyping = true;
        if (!msgList) return;
        var div = document.createElement('div');
        div.className = 'ai-msg-wrap ai-msg-assistant';
        div.id = 'ai-typing-indicator';
        div.innerHTML = '<div class="ai-bubble ai-typing"><span></span><span></span><span></span></div>';
        msgList.appendChild(div);
        scrollBottom();
        requestAnimationFrame(function () { div.classList.add('ai-msg-visible'); });
    }

    function hideTyping() {
        isTyping = false;
        var el = document.getElementById('ai-typing-indicator');
        if (el) el.remove();
    }

    // ── Helpers ───────────────────────────────────────────────────────────
    function scrollBottom() {
        if (msgList) msgList.scrollTop = msgList.scrollHeight;
    }

    // ── Boot ──────────────────────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
