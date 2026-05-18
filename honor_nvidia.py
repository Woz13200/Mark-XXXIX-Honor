import os
import re
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from openai import OpenAI

from remote_android_bridge import (
    call_remote,
    android_status,
    android_vibrate,
    android_speak,
    android_open_url,
    android_home,
    android_back,
    android_recents,
    android_tap,
    android_text,
)


BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")

app = Flask(__name__)
CORS(app)

client = OpenAI(
    base_url=BASE_URL,
    api_key=os.environ.get("NVIDIA_API_KEY", "")
)

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "Tu es MARK XXXIX Honor Edition, un assistant style JARVIS pour Mohammed. "
        "Tu réponds en français, clairement, brièvement, et tu peux contrôler Android via un bridge. "
        "Ne dis jamais qu'une action Android est faite si le bridge ne renvoie pas ok true. "
        "Quand une commande Android est détectée, l'application l'exécute avant de parler."
    )
}

MEMORY = [SYSTEM_MESSAGE]


HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>MARK XXXIX Honor</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    min-height: 100vh;
    background: radial-gradient(circle at top, #16333f 0%, #02070b 58%, #000 100%);
    color: #e9fdff;
    font-family: Arial, sans-serif;
}
header {
    padding: 16px;
    text-align: center;
    border-bottom: 1px solid rgba(0,234,255,.5);
    background: rgba(0,0,0,.35);
    position: sticky;
    top: 0;
    z-index: 2;
}
h1 {
    margin: 0;
    color: #00eaff;
    letter-spacing: 5px;
    text-shadow: 0 0 18px #00eaff;
}
small { color: #86c7d2; }
#orb {
    width: 210px;
    height: 210px;
    border-radius: 50%;
    margin: 24px auto;
    border: 2px solid #00eaff;
    box-shadow: 0 0 50px rgba(0,234,255,.75), inset 0 0 35px rgba(0,234,255,.2);
    position: relative;
    animation: pulse 2.3s infinite;
}
#orb:before {
    content: "";
    position: absolute;
    inset: 36%;
    background: #00eaff;
    border-radius: 50%;
    box-shadow: 0 0 35px #00eaff;
}
#orb:after {
    content: "";
    position: absolute;
    inset: 18%;
    border: 1px dashed rgba(0,234,255,.55);
    border-radius: 50%;
    animation: spin 8s linear infinite;
}
@keyframes pulse {
    0%,100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.045); opacity: .8; }
}
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
main {
    padding: 12px;
    max-width: 900px;
    margin: auto;
}
#chat {
    height: 330px;
    overflow-y: auto;
    border: 1px solid rgba(0,234,255,.35);
    background: rgba(0,10,16,.78);
    border-radius: 14px;
    padding: 12px;
}
.msg {
    margin: 9px 0;
    padding: 11px;
    border-radius: 12px;
    white-space: pre-wrap;
    line-height: 1.35;
}
.user {
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.08);
}
.bot {
    background: rgba(0,234,255,.08);
    border: 1px solid rgba(0,234,255,.35);
}
textarea, input {
    width: 100%;
    margin-top: 9px;
    padding: 13px;
    background: #020a0f;
    color: #fff;
    border: 1px solid rgba(0,234,255,.35);
    border-radius: 12px;
    outline: none;
}
button {
    margin-top: 8px;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #00eaff;
    color: #00eaff;
    background: rgba(0,234,255,.06);
    font-weight: bold;
}
button:active { transform: scale(.98); }
.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}
#log {
    margin-top: 10px;
    height: 155px;
    overflow-y: auto;
    background: rgba(0,0,0,.45);
    border: 1px solid rgba(0,234,255,.25);
    border-radius: 12px;
    padding: 10px;
    color: #a8dce4;
    font-size: 12px;
    white-space: pre-wrap;
}
.badge {
    display: inline-block;
    padding: 5px 8px;
    margin-top: 7px;
    border-radius: 999px;
    border: 1px solid rgba(0,234,255,.35);
    color: #91f4ff;
}
</style>
</head>
<body>
<header>
    <h1>J.A.R.V.I.S</h1>
    <small>MARK XXXIX Honor Fork · NVIDIA · Android Cloudflare Bridge</small><br>
    <span class="badge">Fork: Woz13200/Mark-XXXIX-Honor</span>
</header>

<div id="orb"></div>

<main>
    <div id="chat"></div>

    <textarea id="text" placeholder="Ex: ouvre YouTube, vibre, accueil, retour, parle avec moi..."></textarea>

    <div class="grid">
        <button onclick="sendText()">SEND</button>
        <button onclick="voice()">MIC</button>
        <button onclick="android('status')">STATUS</button>
    </div>

    <h3>Android Control</h3>

    <div class="grid">
        <button onclick="android('vibrate')">VIBRATE</button>
        <button onclick="android('home')">HOME</button>
        <button onclick="android('back')">BACK</button>
        <button onclick="android('recents')">RECENTS</button>
        <button onclick="quickOpen('https://www.youtube.com')">YOUTUBE</button>
        <button onclick="quickOpen('https://www.google.com')">GOOGLE</button>
    </div>

    <input id="url" placeholder="URL à ouvrir sur Honor">
    <button onclick="quickOpen(document.getElementById('url').value)">OPEN URL</button>

    <input id="speakText" placeholder="Texte à dire avec la voix Android">
    <button onclick="android('speak', {text: document.getElementById('speakText').value})">SPEAK ANDROID</button>

    <input id="writeText" placeholder="Texte à écrire sur Android">
    <button onclick="android('text', {value: document.getElementById('writeText').value})">TYPE TEXT</button>

    <div id="log">Android bridge log...</div>
</main>

<script>
const chat = document.getElementById("chat");
const logBox = document.getElementById("log");

function addMsg(role, msg) {
    const d = document.createElement("div");
    d.className = "msg " + role;
    d.textContent = (role === "user" ? "Mohammed: " : "Jarvis: ") + msg;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
}

async function ask(message) {
    addMsg("user", message);
    const r = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message})
    });
    const data = await r.json();
    if (data.android) {
        logBox.textContent = JSON.stringify(data.android, null, 2);
    }
    if (data.error) {
        addMsg("bot", "Erreur: " + data.error);
        return;
    }
    addMsg("bot", data.answer || "");
}

function sendText() {
    const t = document.getElementById("text");
    const msg = t.value.trim();
    if (!msg) return;
    t.value = "";
    ask(msg);
}

function voice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        addMsg("bot", "Reconnaissance vocale indisponible. Utilise Chrome Android.");
        return;
    }
    const rec = new SR();
    rec.lang = "fr-FR";
    rec.start();
    rec.onresult = e => ask(e.results[0][0].transcript);
}

async function android(action, params={}) {
    const r = await fetch("/android", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({action, ...params})
    });
    const data = await r.json();
    logBox.textContent = JSON.stringify(data, null, 2);
}

function quickOpen(url) {
    if (!url) return;
    android("open_url", {url});
}
</script>
</body>
</html>
"""


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def detect_android_command(message: str):
    m = message.lower().strip()

    if any(x in m for x in ["vibre", "vibration", "vibrate"]):
        return "vibrate", {}

    if any(x in m for x in ["accueil", "home screen", "bouton home", "retour accueil"]):
        return "home", {}

    if any(x in m for x in ["retour", "back"]):
        return "back", {}

    if any(x in m for x in ["applications récentes", "recents", "multitâche"]):
        return "recents", {}

    if "youtube" in m or "you tube" in m:
        return "open_url", {"url": "https://www.youtube.com"}

    if "google" in m:
        return "open_url", {"url": "https://www.google.com"}

    if "ouvre" in m and ("http://" in m or "https://" in m or "." in m):
        parts = message.split()
        for p in parts:
            if "." in p or p.startswith("http"):
                return "open_url", {"url": normalize_url(p)}

    if m.startswith("dis ") or m.startswith("parle "):
        return "speak", {"text": message}

    return None, None


def execute_android_action(action, payload):
    if action == "vibrate":
        return android_vibrate()
    if action == "home":
        return android_home()
    if action == "back":
        return android_back()
    if action == "recents":
        return android_recents()
    if action == "open_url":
        return android_open_url(payload.get("url", ""))
    if action == "speak":
        return android_speak(payload.get("text", ""))
    return call_remote(action, payload)


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/ask", methods=["POST"])
def ask():
    if not os.environ.get("NVIDIA_API_KEY"):
        return jsonify({"error": "NVIDIA_API_KEY manquante côté serveur."}), 500

    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Message vide."}), 400

    android_result = None
    action, payload = detect_android_command(message)

    if action:
        android_result = execute_android_action(action, payload or {})
        if action == "open_url":
            if android_result.get("ok"):
                answer = "C’est ouvert sur ton Honor."
            else:
                answer = "J’ai essayé d’ouvrir, mais le bridge Android n’a pas confirmé l’action."
        elif action == "vibrate":
            answer = "Vibration envoyée." if android_result.get("ok") else "La vibration n’a pas été confirmée."
        elif action in ["home", "back", "recents"]:
            answer = "Commande Android exécutée." if android_result.get("ok") else "Commande Android non confirmée."
        elif action == "speak":
            answer = "Je l’ai envoyé à la voix Android." if android_result.get("ok") else "La voix Android n’a pas confirmé."
        else:
            answer = "Commande Android traitée."

        if android_result and android_result.get("ok"):
            android_speak(answer)

        return jsonify({"answer": answer, "android": android_result})

    try:
        MEMORY.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=MODEL,
            messages=MEMORY,
            temperature=0.4,
            max_tokens=900
        )

        answer = response.choices[0].message.content or ""
        MEMORY.append({"role": "assistant", "content": answer})

        speak_result = android_speak(answer)

        return jsonify({
            "answer": answer,
            "android": speak_result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/android", methods=["POST"])
def android():
    data = request.get_json(force=True)
    action = data.get("action")
    payload = dict(data)
    payload.pop("action", None)

    if action == "open_url":
        payload["url"] = normalize_url(payload.get("url", ""))

    result = call_remote(action, payload)
    return jsonify(result)


if __name__ == "__main__":
    print("======================================")
    print(" MARK XXXIX Honor Fork Edition")
    print(" NVIDIA model:", MODEL)
    print(" Local URL: http://0.0.0.0:7860")
    print(" Android bridge URL:", os.environ.get("ANDROID_BRIDGE_URL", "not set"))
    print("======================================")
    app.run(host="0.0.0.0", port=7860)
