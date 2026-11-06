// REPAIRED: Using relative URL since we are running everything on port 8000
const API = "";

// --- STATE MANAGEMENT ---
let isGuest = false;
let currentSessionId = null;
let guestHistory = []; 
let currentUser = null;

// --- DOM ELEMENTS ---
const chatBox = document.getElementById("chat");
const inputField = document.getElementById("msg");
const themeCheckbox = document.getElementById("themeCheckbox");
const themeLabel = document.getElementById("theme-label");

// ==========================================
// LOGIN AUTHENTICATION LOGIC
// ==========================================

const showAuth = (id) => {
    ["start", "login", "signup"].forEach(x => document.getElementById(x).hidden = true);
    document.getElementById(id).hidden = false;
}

async function signup() {
    let n = document.getElementById("n").value;
    let e = document.getElementById("e").value;
    let p = document.getElementById("p").value;
    
    let r = await fetch(API + "/signup", {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: n, email: e, password: p })
    });
    alert((await r.json()).message);
    if(r.ok) showAuth('login');
}

async function login() {
    let e = document.getElementById("le").value;
    let p = document.getElementById("lp").value;
    
    let r = await fetch(API + "/login", {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: e, password: p })
    });
    let d = await r.json();

    if(r.ok) {
        localStorage.token = d.access_token; 
        home("User");
    } else {
        alert(d.detail);
    }
}

function logout() {
    localStorage.removeItem("token");
    currentUser = null;
    isGuest = false;
    currentSessionId = null;
    guestHistory = [];
    chatBox.innerHTML = "";
    document.getElementById("history-list").innerHTML = "";
    
    document.getElementById("chat-wrapper").hidden = true;
    document.getElementById("auth-wrapper").hidden = false;
    showAuth("start");
}

async function home(type) {
    document.getElementById("auth-wrapper").hidden = true;
    document.getElementById("chat-wrapper").hidden = false;
    
    if (type === "Guest") {
        isGuest = true;
        updateSidebarUser("Guest", "Guest", "Temporary Session");
        document.getElementById("history-list").innerHTML = ""; 
    } else {
        isGuest = false;
        let r = await fetch(API + "/profile", { headers: { Authorization: "Bearer " + localStorage.token } });
        if(r.ok) {
            let data = await r.json();
            currentUser = data.user;
            let displayName = currentUser.name || "Satyakam Swami";
            updateSidebarUser(displayName.substring(0, 2).toUpperCase(), displayName, "Premium Access");
            await loadSessions();
        } else {
            alert("Session expired. Please log in again.");
            logout();
        }
    }
}

window.addEventListener('DOMContentLoaded', async () => {
    if (localStorage.token) {
        let r = await fetch(API + "/profile", { headers: { Authorization: "Bearer " + localStorage.token } });
        if(r.ok) { home("User"); }
    }
});


// ==========================================
// AI CHATBOT APP LOGIC
// ==========================================

function updateSidebarUser(avatar, name, status) {
    document.getElementById("sidebar-avatar").innerText = avatar;
    document.getElementById("sidebar-username").innerText = name;
    document.getElementById("sidebar-status").innerText = status;
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("collapsed");
}

function toggleTheme() {
    const isDark = themeCheckbox.checked;
    const newTheme = isDark ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", newTheme);
    themeLabel.innerText = isDark ? "Dark" : "Light";
    localStorage.setItem("theme", newTheme);
}

window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    if (themeCheckbox) {
        themeCheckbox.checked = savedTheme === "dark";
        themeLabel.innerText = savedTheme === "dark" ? "Dark" : "Light";
    }
});

// REPAIRED: Switched to 'keydown' for absolute event blocking
inputField.addEventListener("keydown", (e) => { 
    if (e.key === "Enter") {
        e.preventDefault(); 
        sendMessage(); 
    } 
});

async function clearMemory() {
    if(confirm("Wipe history?")) {
        if(isGuest) {
            guestHistory = [];
            newSession();
        } else {
            await fetch(API + "/clear", { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token: localStorage.token })
            });
            document.getElementById("history-list").innerHTML = "";
            newSession();
        }
    }
}

function newSession() {
    currentSessionId = null;
    chatBox.innerHTML = "";
    if (isGuest) guestHistory = []; 
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    document.getElementById('new-sess-btn').classList.add('active');
}

async function loadSessions() {
    if (isGuest) return;
    let res = await fetch(`${API}/sessions?token=${localStorage.token}`);
    let data = await res.json();
    const historyList = document.getElementById("history-list");
    historyList.innerHTML = "";
    data.sessions.forEach(sess => addSessionToSidebar(sess.session_id, sess.title));
}

function addSessionToSidebar(sessionId, title) {
    const historyList = document.getElementById("history-list");
    let div = document.createElement("div");
    div.className = "nav-item history-item";
    div.id = sessionId;
    div.innerText = title;
    div.onclick = () => loadSessionHistory(sessionId);
    historyList.prepend(div);
}

async function loadSessionHistory(sessionId) {
    if (isGuest) return;
    currentSessionId = sessionId;
    chatBox.innerHTML = "";
    document.querySelectorAll('.history-item, #new-sess-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(sessionId).classList.add('active');
    
    let res = await fetch(`${API}/session/${sessionId}?token=${localStorage.token}`);
    let data = await res.json();
    data.messages.forEach(m => addMessage(m.content, m.role));
}

async function sendMessage() {
    let text = inputField.value.trim();
    if (!text) return;

    addMessage(text, "user");
    inputField.value = "";
    let thinking = addMessage("Thinking...", "ai");

    try {
        let payload = { user_input: text };
        
        if (isGuest) {
            payload.is_guest = true;
            payload.guest_history = guestHistory;
            guestHistory.push({ "role": "user", "content": text });
        } else {
            payload.token = localStorage.token;
            if (currentSessionId) payload.session_id = currentSessionId;
        }

        let res = await fetch(API + "/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        let data = await res.json();
        thinking.remove();
        addMessage(data.reply, "ai");

        if (isGuest) {
            guestHistory.push({ "role": "assistant", "content": data.reply });
            if (!currentSessionId) {
                currentSessionId = "guest_temp";
                addSessionToSidebar(currentSessionId, text.substring(0, 15) + "...");
            }
        } else {
            if (!currentSessionId && data.session_id) {
                currentSessionId = data.session_id;
                addSessionToSidebar(currentSessionId, data.title);
                document.getElementById('new-sess-btn').classList.remove('active');
                document.getElementById(currentSessionId).classList.add('active');
            }
        }

    } catch (err) {
        thinking.remove();
        addMessage("Connection error.", "ai");
    }
}

function addMessage(text, type) {
    let wrapper = document.createElement("div");
    wrapper.className = `message-wrapper ${type}-wrapper`;

    const content = type === "ai" ? marked.parse(text) : text;
    wrapper.innerHTML = `
        <div class="message">${content}</div>
        <div class="meta-tools">
            <span>${text.split(/\s+/).filter(w => w.length > 0).length} Words</span>
            <button class="copy-link" onclick="copyText(this)">Copy</button>
        </div>
    `;

    chatBox.appendChild(wrapper);
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
    return wrapper;
}

function copyText(btn) {
    const text = btn.closest('.message-wrapper').querySelector('.message').innerText;
    navigator.clipboard.writeText(text).then(() => {
        btn.innerText = "Copied!";
        setTimeout(() => btn.innerText = "Copy", 2000);
    });
}