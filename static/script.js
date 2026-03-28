const chatBody = document.getElementById('chat-body');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const resetBtn = document.getElementById('reset-btn');
const voiceBtn = document.getElementById('voice-btn');

const chatPanel = document.querySelector('.chat-panel');
const planPage = document.getElementById('plan-page');
const planBody = document.getElementById('plan-body');
const closePlanBtn = document.getElementById('close-plan-btn');

if (closePlanBtn) {
    closePlanBtn.addEventListener('click', () => {
        planPage.style.display = 'none';
        chatPanel.style.display = 'flex';
        scrollDown();
    });
}

window.showPlanPage = function() {
    chatPanel.style.display = 'none';
    planPage.style.display = 'flex';
};

let sessionId = null;
const FIELDS = ['destination', 'origin', 'date', 'days', 'budget', 'travelers', 'trip_type'];

// ─── Scroll to bottom ───
function scrollDown() {
    chatBody.scrollTo({ top: chatBody.scrollHeight, behavior: 'smooth' });
}

// ─── Add user message ───
function addUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row user-row';
    row.innerHTML = `<div class="bubble user-bubble">${escapeHtml(text)}</div>`;
    chatBody.appendChild(row);
    scrollDown();
}

// ─── Add bot message (text) ───
function addBotMessage(html) {
    const row = document.createElement('div');
    row.className = 'msg-row bot-row';
    row.innerHTML = `
        <div class="avatar-sm">AI</div>
        <div class="bubble bot-bubble">${html}</div>
    `;
    chatBody.appendChild(row);
    scrollDown();
    
    // Voice assistance: speak the text content (not HTML)
    const textToSpeak = row.innerText.replace("AI", "").trim();
    speakText(textToSpeak);
    
    return row;
}

// ─── Show typing indicator ───
function showTyping() {
    const row = document.createElement('div');
    row.className = 'msg-row bot-row typing-row';
    row.innerHTML = `
        <div class="avatar-sm">AI</div>
        <div class="bubble bot-bubble typing-bubble">
            <div class="typing-dots"><span></span><span></span><span></span></div>
        </div>
    `;
    chatBody.appendChild(row);
    scrollDown();
    return row;
}

// ─── Update Memory Panel ───
function updateMemory(memory) {
    if (!memory) return;
    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val || '—';
    };
    set('m-origin', memory.origin);
    set('m-dest', memory.destination);
    set('m-date', memory.date);
    set('m-days', memory.days);
    set('m-budget', memory.budget ? `₹${parseInt(memory.budget).toLocaleString('en-IN')}` : '');
    set('m-travelers', memory.travelers);
    set('m-type', memory.trip_type);

    const filled = FIELDS.filter(f => memory[f]).length;
    const pct = Math.round((filled / FIELDS.length) * 100);
    document.getElementById('readiness-fill').style.width = pct + '%';
    document.getElementById('readiness-pct').textContent = pct + '%';

    const badge = document.getElementById('status-badge');
    if (pct === 100) {
        badge.textContent = 'Complete ✅';
        badge.classList.add('ready');
    } else {
        badge.textContent = 'Gathering Info';
        badge.classList.remove('ready');
    }
}

// ─── Render Final Plan ───
function renderPlan(data) {
    // Summary message for the Chat
    const summary = data.trip_summary;
    addBotMessage(`
        <strong>✅ ${data.message}</strong><br>
        <small style="color:var(--muted)">
            ${summary.from} → ${summary.to} | ${summary.date} | ${summary.travelers} traveler(s)
        </small>
        <div style="margin-top: 0.8rem;">
            <button onclick="showPlanPage()" style="background: var(--green); color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 0.85rem;">View Best Plan & Itinerary ↗</button>
        </div>
    `);

    currentPlanData = data;
    let planHtml = '';

    // Budget Breakdown
    const b = data.budget_breakdown;
    planHtml += `
        <div class="result-block" style="max-width: 100%;">
        <p class="section-title">💰 Budget Breakdown</p>
        <div class="budget-grid" style="grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));">
            <div class="budget-item">
                <div class="budget-label">Total Allocated Budget</div>
                <div class="budget-value" style="color:var(--primary); font-size:1.6rem;">${b.total}</div>
            </div>
            <div class="budget-item"><div class="budget-label">Per Person</div><div class="budget-value">${b.per_person}</div></div>
            <div class="budget-item"><div class="budget-label">🚆 Transport</div><div class="budget-value">${b.transport}</div></div>
            <div class="budget-item"><div class="budget-label">🏨 Hotel (Total Stay)</div><div class="budget-value">${b.hotel}</div></div>
            <div class="budget-item"><div class="budget-label">🍽️ Food & Misc</div><div class="budget-value">${b.food_misc}</div></div>
        </div>
        </div>
        </div>
    `;

    // Travel Options
    let optHtml = `<div class="result-block" style="max-width: 100%;"><p class="section-title" style="margin-top: 1.5rem;">✈️ 🚂 🚌 Travel Options</p>`;
    data.travel_options.forEach(opt => {
        const badgeClass = opt.type === 'fastest' ? 'badge-fastest' : opt.type === 'cheapest' ? 'badge-cheapest' : 'badge-budget';
        const altChips = (opt.alt_links || []).map(a =>
            `<a href="${a.url}" target="_blank" rel="noopener" class="btn-alt">${a.label} ↗</a>`
        ).join('');
        optHtml += `
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${opt.mode}</span>
                    <span class="card-type-badge ${badgeClass}">${opt.type}</span>
                </div>
                <div class="card-meta">Total: ${opt.total_cost} &nbsp;•&nbsp; Per Person: ${opt.cost_per_person} &nbsp;•&nbsp; ${opt.duration}</div>
                ${opt.note ? `<div class="card-note">${opt.note}</div>` : ''}
                <div class="card-actions">
                    <a href="${opt.booking_link}" target="_blank" rel="noopener" class="btn-book">🎫 Book on ${opt.platform} →</a>
                    ${altChips}
                </div>
            </div>
        `;
    });
    optHtml += `</div>`;
    planHtml += optHtml;

    // Hotels
    let hotelHtml = `<div class="result-block" style="max-width: 100%;"><p class="section-title" style="margin-top: 1.5rem;">🏨 Hotel Options</p>`;
    data.hotels.forEach(h => {
        const altChips = (h.alt_links || []).map(a =>
            `<a href="${a.url}" target="_blank" rel="noopener" class="btn-alt">${a.label} ↗</a>`
        ).join('');
        hotelHtml += `
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${h.emoji} ${h.name}</span>
                    <div style="text-align:right">
                        <span class="card-price">${h.price_per_night}/night</span><br/>
                        <span style="font-size:0.8rem; color:var(--text-muted); font-weight:bold">${h.total_stay_price || ''}</span>
                    </div>
                </div>
                <div class="card-meta">${h.category} &nbsp;•&nbsp; ${h.location}</div>
                <div class="card-actions">
                    <a href="${h.booking_link}" target="_blank" rel="noopener" class="btn-book">🏨 Book on MakeMyTrip →</a>
                    ${altChips}
                </div>
            </div>
        `;
    });
    hotelHtml += `</div>`;
    planHtml += hotelHtml;

    // Events & Activities
    if (data.events && data.events.length > 0) {
        let evHtml = `<div class="result-block" style="max-width: 100%;"><p class="section-title" style="margin-top: 1.5rem;">🎉 Top Events & Things to Do in ${data.trip_summary.to}</p><div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">`;
        data.events.forEach(e => {
            evHtml += `
                <div class="card" style="padding: 1.2rem; border-left: 3px solid #64ffda;">
                    <strong style="display:block; margin-bottom: 0.5rem; color: #fff; font-size: 1rem;">${e.title}</strong>
                    <p style="font-size: 0.9rem; margin-bottom: 0.8rem; color: var(--text-muted); line-height: 1.4;">${e.description}</p>
                    <span style="font-size: 0.75rem; font-weight: 500; padding: 0.2rem 0.5rem; background: rgba(255,255,255,0.08); border-radius: 4px; color: #64ffda;">🏷️ ${e.price}</span>
                </div>
            `;
        });
        evHtml += `</div></div>`;
        planHtml += evHtml;
    }

    // Itinerary
    let itiHtml = `<div class="result-block" style="max-width: 100%;"><p class="section-title" style="margin-top: 1.5rem;">📅 Day-wise Itinerary</p><div class="timeline">`;
    
    let startDateObj = new Date();
    if (data.trip_summary.date && data.trip_summary.date.includes("-")) {
        const [y, m, d] = data.trip_summary.date.split('-');
        startDateObj = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
    }

    data.itinerary.forEach(day => {
        let activeDate = new Date(startDateObj);
        activeDate.setDate(startDateObj.getDate() + (day.day - 1));
        let ds = activeDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

        const places = (day.places || []).map(p => `<span class="place-tag">${p}</span>`).join('');
        itiHtml += `
            <div class="timeline-item">
                <div class="timeline-day" style="display:flex; justify-content:space-between; align-items:baseline;">
                    <span>Day ${day.day}: ${day.theme}</span>
                    <span style="font-size: 0.82rem; color: #64ffda; font-weight: normal; background: rgba(255,255,255,0.08); padding: 3px 8px; border-radius: 4px; letter-spacing: 0.4px;">🗓️ ${ds}</span>
                </div>
                <div class="timeline-plan">${day.plan}</div>
                <div class="places-list">${places}</div>
            </div>
        `;
    });
    itiHtml += `</div></div>`;
    planHtml += itiHtml;

    // Suggestions / Advisory
    if (data.travel_advisory) {
        planHtml += `
            <div class="result-block" style="max-width: 100%; margin-bottom: 2rem;">
            <p class="section-title" style="margin-top: 1.5rem;">💡 Travel Suggestions & Advisory</p>
            <div class="advisory">⚠️ ${data.travel_advisory}</div>
            
            <p class="section-title" style="margin-top: 2rem;">📊 Final Expenditure Benchmarking</p>
            <div style="background:rgba(255,255,255,0.03); border-radius:16px; border:1px solid var(--border); overflow:hidden;">
                <div style="display:grid; grid-template-columns: 1fr 1fr;">
                    <div style="padding:1.5rem; background:rgba(60,132,246,0.05); border-right:1px solid var(--border);">
                        <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:var(--primary); margin-bottom:0.5rem;">Your Budget</div>
                        <div style="font-size:1.8rem; font-weight:900; color:var(--primary); font-family:monospace;">${b.total}</div>
                        <p style="font-size:0.8rem; font-weight:600; color:var(--text); margin-top:0.8rem;">💎 Experience Level:</p>
                        <ul style="font-size:0.75rem; color:var(--text-muted); padding-left:1.2rem; margin-top:0.4rem;">
                            <li>Optimized Stays (${b.per_night_info})</li>
                            <li>Efficient Comfort Transit</li>
                            <li>Financial buffer for dining & activities</li>
                        </ul>
                    </div>
                    <div style="padding:1.5rem;">
                        <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted); margin-bottom:0.5rem;">Lowest Budget Possible</div>
                        <div style="font-size:1.8rem; font-weight:900; color:var(--green); font-family:monospace;">${data.price_tiers.economic}</div>
                        <p style="font-size:0.8rem; font-weight:600; color:var(--text-muted); margin-top:0.8rem;">📉 Survival Tier:</p>
                        <ul style="font-size:0.75rem; color:var(--red); padding-left:1.2rem; margin-top:0.4rem;">
                            <li>Non-AC Sleeper Coach only</li>
                            <li>Budget Dorms / Survival Stays</li>
                            <li>Minimal food liquidity</li>
                        </ul>
                    </div>
                </div>
            </div>
            </div>
        `;
    }

    if (planBody) {
        planBody.innerHTML = planHtml;
    }
    
    // Automatically transition to the plan page
    setTimeout(window.showPlanPage, 1200);
}

// ─── Escape HTML ───
function escapeHtml(text) {
    return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── Disable / Enable Input ───
function setLoading(loading) {
    userInput.disabled = loading;
    sendBtn.disabled = loading;
}

// ─── Form Submit ───
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    addUserMessage(text);
    userInput.value = '';
    setLoading(true);

    const typingEl = showTyping();

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, session_id: sessionId || '' })
        });

        const data = await res.json();
        typingEl.remove();

        sessionId = data.session_id;
        updateMemory(data.memory);

        if (data.status === 'incomplete') {
            addBotMessage(data.message);
        } else if (data.status === 'complete') {
            // Brief delay for dramatic effect
            const t2 = showTyping();
            setTimeout(() => {
                t2.remove();
                renderPlan(data);
            }, 800);
        }
    } catch (err) {
        typingEl.remove();
        addBotMessage('⚠️ Could not reach the server. Make sure the backend is running on port 8000.');
    } finally {
        setLoading(false);
        userInput.focus();
    }
});

// ─── Reset Session ───
resetBtn.addEventListener('click', async () => {
    if (sessionId) {
        await fetch(`/session/${sessionId}`, { method: 'DELETE' }).catch(() => {});
    }
    sessionId = null;
    chatBody.innerHTML = `
        <div class="msg-row bot-row">
            <div class="avatar-sm">AI</div>
            <div class="bubble bot-bubble">
                Fresh start! 🌟 Where would you like to travel to next?
            </div>
        </div>
    `;
    updateMemory({ destination:'', origin:'', date:'', days:'', budget:'', travelers:'', trip_type:'' });
});

// ─── Interactive Budget Recalculation ───
window.recalculateBudget = function(from, to) {
    const input = document.getElementById('budget-updater');
    const newBudgetStr = input.value.replace(/[^0-9]/g, '');
    if (!newBudgetStr) return alert("Please enter a valid budget amount!");
    
    // Construct new intelligent query
    const newQuery = `Trip from ${from} to ${to} under ₹${newBudgetStr}`;
    
    // Switch back to Chat View and trigger search
    showChatPage();
    document.getElementById('user-input').value = newQuery;
    sendMessage();
};

// ─── Voice Assistance (STT & TTS) ───
let recognition;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-IN';

    recognition.onstart = () => {
        voiceBtn.classList.add('recording');
        userInput.placeholder = "Listening...";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        userInput.placeholder = "Speak or type your destination...";
        sendMessage(); // Auto-send
    };

    recognition.onend = () => {
        voiceBtn.classList.remove('recording');
        userInput.placeholder = "Speak or type your destination...";
    };

    recognition.onerror = () => {
        voiceBtn.classList.remove('recording');
        userInput.placeholder = "Speak or type your destination...";
    };
}

if (voiceBtn) {
    voiceBtn.addEventListener('click', () => {
        if (!recognition) return alert("Speech recognition not supported in this browser.");
        recognition.start();
    });
}

function speakText(text) {
    if (!('speechSynthesis' in window)) return;
    
    // Pre-calculate to avoid long speeches for technical results
    const shortText = text.substring(0, 200) + (text.length > 200 ? "..." : "");
    
    // Stop any existing speech
    window.speechSynthesis.cancel();
    
    const msg = new SpeechSynthesisUtterance(shortText);
    msg.rate = 1.0;
    msg.pitch = 1.0;
    msg.volume = 0.8;
    
    // Find a nice English voice
    const voices = window.speechSynthesis.getVoices();
    const indVoice = voices.find(v => v.lang.includes('en-IN')) || voices.find(v => v.lang.includes('en-US'));
    if (indVoice) msg.voice = indVoice;
    
    window.speechSynthesis.speak(msg);
}
