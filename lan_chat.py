

from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv()
#!/usr/bin/env python3
"""
LAN Anonymous Chat – single-file Python app

Features
- Web chat for anyone on your local network
- Anonymous auto-assigned nicknames (e.g., "calm-otter-42")
- Real-time messages via WebSockets (Socket.IO)
- Typing indicator
- Simple, responsive UI (no build step)

Usage
1) pip install -U flask flask-socketio eventlet itsdangerous
2) python lan_chat.py
3) On the same network, open http://<your-LAN-IP>:5000 in a browser

Security note: This is a lightweight demo. Do not expose to the public Internet
without adding auth, rate limiting, TLS, and hardening.
"""

import secrets
import socket
from datetime import datetime, UTC
from typing import Dict, Set


from flask import Flask, request, make_response, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import jsonify
from werkzeug.utils import secure_filename


# Load AI config from environment
AI_API_TYPE = os.getenv("AI_API_TYPE", "lmstudio")
AI_API_URL = os.getenv("AI_API_URL", "http://localhost:1234/v1/chat/completions")
AI_MODEL = os.getenv("AI_MODEL", "your-model-name")
AI_NAME = os.getenv("AI_NAME", "LanAI")
AI_FULL_NAME = os.getenv("AI_FULL_NAME", "LanAI Bot")

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    print('[DEBUG] upload_file called')
    print(f'[DEBUG] request.method: {request.method}')
    print(f'[DEBUG] request.headers: {dict(request.headers)}')
    print(f'[DEBUG] request.files: {request.files}')
    if 'file' not in request.files:
        print('[DEBUG] No file part in request.files:', request.files)
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    print(f'[DEBUG] file.filename: {file.filename}')
    if file.filename == '':
        print('[DEBUG] No selected file')
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print(f'[DEBUG] Saving file as: {filename}')
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        url = f"/uploads/{filename}"
        print(f'[DEBUG] File saved, url: {url}')
        return jsonify({'url': url}), 200
    print('[DEBUG] Invalid file type:', file.filename)
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



# Serve upload_test.html for upload testing
@app.route('/upload_test.html')
def upload_test():
    return send_from_directory(os.path.dirname(__file__), 'upload_test.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, filename)
app.config["SECRET_KEY"] = secrets.token_hex(16)
# eventlet is the simplest for local realtime; you can swap to gevent if you like
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# In-memory state (good enough for a single-process LAN demo)
USERS: Dict[str, str] = {}  # sid -> nickname
TYPING: Set[str] = set()    # set of sids currently typing
ROOM = "main"

ADJECTIVES = [
    "brisk", "calm", "candid", "cheerful", "chill", "clever", "cozy", "daring",
    "eager", "gentle", "glowing", "humble", "keen", "lucky", "merry", "nifty",
    "plucky", "quirky", "rapid", "snug", "spry", "sunny", "swift", "vivid"
]
ANIMALS = [
    "otter", "panda", "lynx", "koala", "falcon", "fox", "tiger", "badger",
    "heron", "narwhal", "yak", "eagle", "orca", "gecko", "lemur", "llama",
    "ram", "sparrow", "seal", "marten", "beaver", "ibis", "bison", "dingo"
]

def random_nickname() -> str:
    return f"{secrets.choice(ADJECTIVES)}-{secrets.choice(ANIMALS)}-{secrets.randbelow(100)}"

# -------------------- HTTP route (serves UI) --------------------
@app.route("/")
def index():
    # Set a cookie so reconnects keep the same nickname during a browser session
    nickname = request.cookies.get("nickname") or random_nickname()
    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>LAN Chat</title>
        <style>
            :root {{
                --bg: #0f172a;
                --panel: #111827;
                --muted: #94a3b8;
                --text: #e5e7eb;
                --accent: #22d3ee;
                --me: #10b981;
                --other: #3b82f6;
            }}
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif; background: var(--bg); color: var(--text); }}
            .wrap {{ min-height: 100dvh; display: grid; grid-template-columns: 0px 85vw; grid-template-rows: auto 1fr auto; }}
            header {{ grid-column: 1 / span 2; padding: 12px 16px; background: var(--panel); border-bottom: 1px solid #1f2937; display:flex; gap:12px; align-items:center; }}
            header h1 {{ margin: 0; font-size: 18px; letter-spacing: 0.3px; }}
            header .chip {{ padding: 4px 10px; background:#0b3b3c; border:1px solid #124e51; border-radius:999px; font-size:12px; color:#a7f3d0; }}
            .sidebar h2 {{ font-size: 14px; margin: 0 0 8px 0; color: var(--muted); }}
            #user-list {{ list-style: none; padding: 0; margin: 0; }}
                #user-list li {{ font-size: 12px; color: var(--text); padding: 2px 0; border-bottom: 1px solid #222; }}
                #messages {{ list-style: none; margin:0; padding: 16px; display:flex; flex-direction:column; gap:10px; width:85%; }}
                #messages li {{ max-width: 800px; padding: 10px 12px; border-radius: 12px; background: #0b1220; box-shadow: 0 1px 0 #1f2937 inset; }}
                #messages li.me {{ border: 1px solid rgba(16,185,129,.35); }}
                #messages li.other {{ border: 1px solid rgba(59,130,246,.35); }}
                .meta {{ font-size: 11px; color: var(--muted); margin-bottom: 4px; }}
                .footer {{ grid-column: 2; padding: 12px; background: var(--panel); border-top: 1px solid #1f2937; }}
                form {{ display:flex; gap:10px; }}
                input[type=text] {{ flex:1; padding: 12px 14px; border-radius: 10px; border:1px solid #374151; background:#0b1220; color:var(--text); outline:none; }}
                button {{ padding: 12px 16px; border-radius: 10px; border:none; background: var(--accent); color:#05252b; font-weight: 700; cursor: pointer; }}
                #typing {{ height: 20px; padding: 0 16px; font-size: 12px; color: var(--muted); }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <header>
                <h1>LAN Chat</h1>
                <span class="chip">You are <strong id="me-name">{nickname}</strong></span>
            </header>
            <!-- Online users sidebar removed -->
            <main style="grid-column: 2; width: 85vw;">
                <ul id="messages"></ul>
                <div id="typing"></div>
                <div class="footer">
                    <form id="form">
                        <input id="input" type="text" autocomplete="off" placeholder="Type a message…" />
                        <button>Send</button>
                    </form>
                </div>
            </main>
        </div>

    <script src="https://cdn.jsdelivr.net/npm/socket.io-client@3.1.3/dist/socket.io.min.js"></script>
        <script>window.nickname = "{nickname}";</script>
    <script src="/static/lan_chat.js"></script>
    <script src="/static/upload.js"></script>
    </body>
    </html>
    """

    resp = make_response(html)
    resp.set_cookie("nickname", nickname, httponly=False, samesite="Lax")
    return resp

# -------------------- Socket.IO events --------------------
@socketio.on("join")
def on_join(data):
    sid = request.sid
    nickname = (data or {}).get("nickname") or random_nickname()
    print(f"[DEBUG] on_join: sid={sid}, nickname={nickname}")
    USERS[sid] = nickname
    print(f"[DEBUG] USERS after join: {USERS}")
    join_room(ROOM)
    emit("user_count", len(USERS), to=ROOM)
    emit("user_list", list(USERS.values()), to=ROOM)
    emit(
        "chat",
        {"nickname": "system", "text": f"{nickname} joined", "ts": datetime.now(UTC).isoformat()},
        to=ROOM,
    )

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    print(f"[DEBUG] on_disconnect: sid={sid}")
    nickname = USERS.pop(sid, None)
    print(f"[DEBUG] USERS after disconnect: {USERS}")
    TYPING.discard(sid)
    if nickname:
        emit(
            "chat",
            {"nickname": "system", "text": f"{nickname} left", "ts": datetime.now(UTC).isoformat()},
            to=ROOM,
        )
        emit("typing", {"list": [USERS[s] for s in TYPING if s in USERS]}, to=ROOM)
        emit("user_count", len(USERS), to=ROOM)
        emit("user_list", list(USERS.values()), to=ROOM)

@socketio.on("chat")
def on_chat(data):
    sid = request.sid
    nickname = USERS.get(sid, random_nickname())
    text = (data or {}).get("text", "").strip()

    if not text:
        return

    payload = {"nickname": nickname, "text": text[:2000], "ts": datetime.now(UTC).isoformat()}
    emit("chat", payload, to=ROOM)

@socketio.on("typing")
def on_typing(data):
    sid = request.sid
    state = bool((data or {}).get("state"))
    if state:
        TYPING.add(sid)
    else:
        TYPING.discard(sid)
    emit("typing", {"list": [USERS[s] for s in TYPING if s in USERS]}, to=ROOM)

# -------------------- Utilities --------------------

def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        try:
            s.close()
        except Exception:
            pass
    return ip



# -------------------- Entrypoint --------------------
if __name__ == "__main__":
    ip = get_lan_ip()
    print("\nLAN Chat running!")
    print(f"Open  ->  http://{ip}:5000  (from any device on your LAN)\n")
    socketio.run(app, host="0.0.0.0", port=5000)
