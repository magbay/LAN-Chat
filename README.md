# LAN Chat App

A simple, anonymous real-time chat application for your local network, built with Python, Flask, and Socket.IO. Supports text and image messages, user count, and image uploads.

---

## Features
- **Anonymous chat:** Auto-generated nicknames for privacy
- **Real-time messaging:** Instant updates via WebSockets (Socket.IO)
- **Image upload:** Upload and share images directly in chat
- **User count:** See how many users are online
- **Typing indicator:** See when others are typing
- **No registration:** Just open the app and chat
- **LAN only:** Designed for local network use (not secure for public internet)

---

## Setup Guide

### 1. Clone the repository
```bash
git clone https://github.com/magbay/LAN-Chat.git
cd LAN-Chat
```

### 2. Create and activate a Python virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, create one with:
```
flask
flask-socketio
eventlet
itsdangerous
```

### 4. Run the app
```bash
python lan_chat.py
```

### 5. Open in your browser
- On the same machine: [http://localhost:5000](http://localhost:5000)
- On other devices in your LAN: `http://<your-LAN-IP>:5000`
  - The server will print your LAN IP on startup.

---

## How the Code Works

### Main Components
- **lan_chat.py**: Main Flask app, handles HTTP routes, Socket.IO events, and image upload endpoints.
- **static/lan_chat.js**: Frontend chat logic (connects to Socket.IO, renders messages, handles UI).
- **static/upload.js**: Handles image upload and emits image URLs to chat.
- **uploads/**: Stores uploaded images.

### Key Code Sections
- **Flask app setup:**
  - `app = Flask(__name__)`
  - Registers routes for `/`, `/upload`, `/uploads/<filename>`, `/static/`, etc.
- **Socket.IO:**
  - Handles `join`, `disconnect`, `chat`, and `typing` events.
  - Broadcasts messages and user count to all clients.
- **Image upload:**
  - POST to `/upload` saves the file to `uploads/` and returns a URL.
  - The frontend emits this URL as a chat message.
- **Frontend:**
  - Connects to Socket.IO, renders messages, detects and displays images, shows user count and typing status.

### Security Note
- This app is for LAN/demo use only. Do **not** expose to the public internet without adding authentication, HTTPS, and security hardening.

---

## Troubleshooting
- If you get `ModuleNotFoundError`, ensure you activated your virtual environment and installed requirements.
- If image upload fails, check that the `uploads/` directory exists and is writable.
- If chat doesn't update, check browser console for errors and ensure Socket.IO client version matches the server.

---

## Example requirements.txt
```
flask
flask-socketio
eventlet
itsdangerous
```

---

## License
MIT
