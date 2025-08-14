# README2: Beginner's Guide to lan_chat.py and ai_user.py

This guide explains, line by line and in plain language, how the two main files in this chat app work:
- `lan_chat.py`: The main chat server and web app
- `ai_user.py`: The AI bot that joins the chat and replies to users

---

## lan_chat.py (The Chat Server)

**Imports and Setup**
- `from __future__ import annotations`: Enables some future Python features.
- `import os`, `import secrets`, `import socket`, etc.: Loads standard Python modules for environment, security, networking, and time.
- `from dotenv import load_dotenv`: Lets you load settings from a `.env` file.
- `load_dotenv()`: Loads environment variables from `.env`.
- `from flask import ...`: Imports Flask, a web framework for Python.
- `from flask_socketio import ...`: Imports Flask-SocketIO for real-time chat.
- `from werkzeug.utils import secure_filename`: Helps safely save uploaded files.

**AI Config**
- Loads AI settings (like model and API URL) from environment variables.

**Flask App and Uploads**
- `app = Flask(__name__)`: Creates the web app.
- Sets up a folder for image uploads and allowed file types.
- Functions to check if a file is allowed and to handle uploads.
- Routes to serve uploaded files and static files.

**Web UI**
- The `/` route serves a simple HTML chat page with a nickname and chat box.
- The HTML includes CSS for styling and JavaScript for chat features.

**Socket.IO Events**
- Handles real-time events:
  - `join`: When a user joins, assigns a nickname and notifies others.
  - `disconnect`: When a user leaves, removes them and notifies others.
  - `chat`: When a user sends a message, broadcasts it to everyone.
  - `typing`: Shows who is typing.

**Utilities**
- `random_nickname()`: Makes fun nicknames like "calm-otter-42".
- `get_lan_ip()`: Finds your computer's LAN IP address.

**Entrypoint**
- If you run this file directly, it starts the server and prints the URL to join the chat from any device on your network.

---

## ai_user.py (The AI Bot)

**Imports and Setup**
- Loads modules for networking, random numbers, HTTP requests, and environment variables.
- Loads settings from `.env` and prints them for debugging.
- Picks a random nickname for the AI bot.
- Connects to the chat server using Socket.IO.

**Socket.IO Events**
- `connect`: When the AI bot connects, it joins the chat room.
- `chat`: When a message is received, the bot decides if it should reply:
  - Ignores its own messages and system messages.
  - Replies if its name is mentioned, if the message is a question, or at random.
  - Sends a reply using the `generate_reply` function.
  - Sometimes sends a fun fact or tip.
- `disconnect`: Prints a message if the bot disconnects.

**AI Reply Logic**
- `generate_reply(prompt)`: Sends the user's message to the AI API (Ollama or LM Studio) and gets a reply.
  - Tries multiple times if the model is still loading.
  - Handles errors and prints debug info.

**Testing the AI**
- `test_ollama_model()`: Lets you test if the AI model is ready by running `python ai_user.py test`.

**Entrypoint**
- If you run this file directly, it either runs the test or connects the bot to the chat server and keeps it running.

---

## ai_user.py (AI Bot) - Full Code with Comments

```python
import os  # For environment variables
import sys  # For system-specific parameters and functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Add current directory to Python path
from lan_chat import random_nickname  # Import nickname generator from lan_chat.py
import time  # For time-related functions (like sleep)
import random  # For random number generation
import requests  # For making HTTP requests to the AI API
import socketio  # For connecting to the chat server via Socket.IO
from dotenv import load_dotenv  # For loading environment variables from .env file

load_dotenv()  # Load environment variables from .env file

# Print out the current configuration for debugging
print("[AI] Startup configuration:")
print(f"[AI]   API_TYPE: {os.getenv('AI_API_TYPE')}")
print(f"[AI]   API_URL:  {os.getenv('AI_API_URL')}")
print(f"[AI]   MODEL:    {os.getenv('AI_MODEL')}")
print(f"[AI]   SERVER:   {os.getenv('AI_SERVER_URL')}")

# Read configuration from environment variables, with defaults
AI_API_TYPE = os.getenv("AI_API_TYPE", "ollama")
AI_API_URL = os.getenv("AI_API_URL", "http://10.107.101.37:11434/v1/chat/completions")
AI_MODEL = os.getenv("AI_MODEL", "qwen3:8b")
AI_NAME = random_nickname()  # Generate a random nickname for the AI bot
AI_FULL_NAME = os.getenv("AI_FULL_NAME", "LanAI Bot")
SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:5000")

sio = socketio.Client()  # Create a Socket.IO client instance

last_message_ts = None  # Track the timestamp of the last message

@sio.event
# This function runs when the AI bot connects to the chat server
# It joins the chat room with its nickname
def connect():
    print(f"[AI] Connected to chat server as {AI_NAME}")
    sio.emit("join", {"nickname": AI_NAME})
    # Do not send any initial response after login

@sio.event
# This function runs when a chat message is received
# It decides whether the AI should reply
# It ignores its own messages and system messages
# Replies if its name is mentioned, if the message is a question, or at random
# Sometimes sends a fun fact or tip
# Uses generate_reply() to get a response from the AI model
# Sends the reply back to the chat
# Also prints debug info
#
def chat(data):
    global last_message_ts
    print(f"[AI] Received chat event: {data}")
    nickname = data.get("nickname", "")
    text = data.get("text", "")
    ts = data.get("ts", "")
    # Ignore system messages, own messages, and system events
    if nickname == AI_NAME or nickname.lower() == "system":
        return
    if any(event in text.lower() for event in ["joined", "left"]):
        return

    # Respond if AI's name or any part of its name is mentioned
    name_parts = [part.lower() for part in AI_NAME.replace('-', ' ').split()]
    text_words = [word.lower() for word in text.replace('-', ' ').split()]
    mentioned = AI_NAME.lower() in text.lower() or AI_FULL_NAME.lower() in text.lower() or any(part in text_words for part in name_parts)

    # Respond if message is a question
    is_question = '?' in text or text.strip().lower().startswith((
        'how', 'what', 'why', 'when', 'where', 'who', 'is', 'are', 'can', 'do', 'does', 'did', 'will', 'should', 'could', 'would', 'may', 'might'))

    # Configurable response probability
    RESPONSE_PROBABILITY = float(os.getenv("AI_RESPONSE_PROBABILITY", "0.1"))
    random_response = random.random() < RESPONSE_PROBABILITY

    # Respond if directly mentioned, or if message contains any part of AI's name and is a question, or random chance
    name_in_question = any(part in text_words for part in name_parts) and is_question
    if mentioned or name_in_question or random_response:
        # Always use the actual message content and append concise answer instructions
        prompt = f"{text}\nAnswer concisely and directly. Only provide the answer, no extra commentary."
        print(f"[AI] Responding to message from '{nickname}': {text}")
        reply = generate_reply(prompt)
        print(f"[AI] Reply generated: {reply}")
        sio.emit("chat", {"text": reply})

    # Occasionally add random short informational messages
    if random.random() < 0.1:  # 10% chance per message event
        info_messages = [
            "Did you know? The honeybee is the only insect that produces food eaten by humans.",
            "Tip: You can drag and drop images to share them here!",
            "Fun fact: The Eiffel Tower can be 15 cm taller during hot days.",
            "Reminder: Stay hydrated!",
            "Did you know? Octopuses have three hearts.",
            "Tip: Use @username to get someone's attention.",
            "Fact: Bananas are berries, but strawberries aren't.",
            "Did you know? A group of flamingos is called a 'flamboyance'.",
            "Tip: You can use emojis in your messages!",
            "Fact: The shortest war in history lasted 38 minutes.",
        ]
        info = random.choice(info_messages)
        sio.emit("chat", {"text": info})

@sio.event
# This function runs when the AI bot disconnects from the chat server
# It just prints a message
#
def disconnect():
    print("[AI] Disconnected from chat server.")

# This function sends a prompt to the AI API and returns the reply
# It supports both LM Studio and Ollama APIs
# It retries if the model is still loading
# Handles errors and prints debug info
#
def generate_reply(prompt):
    if AI_API_TYPE == "lmstudio":
        prompt_limited = f"{prompt}\nAnswer concisely and directly. Only provide the answer, no extra commentary."
        payload = {
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt_limited}],
            "temperature": 0.4
        }
        print(f"[AI] Sending request to LM Studio API: {AI_API_URL} with payload: {payload}")
        try:
            r = requests.post(AI_API_URL, json=payload, timeout=10)
            print(f"[AI] API response status: {r.status_code}")
            print(f"[AI] API response text: {r.text}")
            r.raise_for_status()
            data = r.json()
            if "choices" not in data or not data["choices"]:
                print("[AI] Full response (no 'choices'):", data)
                return f"[AI error: No 'choices' in response: {data}]"
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AI] Exception during API call: {e}")
            return f"[AI error: {e}]"
    elif AI_API_TYPE == "ollama":
        prompt_limited = f"{prompt}\nYou are a helpful, friendly, and concise chat assistant."
        payload = {
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt_limited}]
        }
        # Configurable retries and wait time
        max_retries = int(os.getenv("OLLAMA_RETRIES", 10))
        retry_wait = int(os.getenv("OLLAMA_RETRY_WAIT", 5))
        for attempt in range(max_retries):
            print(f"[AI] Sending request to Ollama API: {AI_API_URL} with payload: {payload} (attempt {attempt+1}/{max_retries})")
            try:
                r = requests.post(AI_API_URL, json=payload, timeout=30)
                print(f"[AI] API response status: {r.status_code}")
                print(f"[AI] API response text: {r.text}")
                r.raise_for_status()
                data = r.json()
                reply = None
                if "choices" in data and data["choices"]:
                    reply = data["choices"][0].get("text") or data["choices"][0].get("message", {}).get("content")
                elif data.get("response") is not None:
                    reply = data["response"]
                # Retry if model is still loading or reply is empty
                if data.get("done_reason") == "load" or (reply is not None and str(reply).strip() == ""):
                    print(f"[AI] Model still loading, waiting {retry_wait}s before retry... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_wait)
                    continue
                if reply:
                    return str(reply).strip()
                print("[AI] Full response (no usable reply):", data)
                return "[No response from model]"
            except Exception as e:
                print(f"[AI] Exception during API call: {e}")
                time.sleep(retry_wait)
        return "[No response from model after retries]"
    else:
        return "[AI not configured]"

# This function tests if the AI model is ready and can generate a response
# You can run it with: python ai_user.py test
def test_ollama_model():
    """Test if Ollama model is ready and can generate a response."""
    test_message = "Hello, are you there?"
    print("[TEST] Testing Ollama model with a simple prompt...")
    reply = generate_reply(test_message)
    if reply and not reply.startswith('[No response'):
        print(f"[TEST] Model reply: {reply}")
        print("[TEST] Ollama model is ready and functional.")
        return True
    else:
        print("[TEST] Model did not reply after retries. It may still be loading or unavailable.")
        return False

# Main entrypoint: if run directly, either test the model or connect to the chat server
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_ollama_model()
    else:
        while True:
            try:
                sio.connect(SERVER_URL)
                sio.wait()
            except Exception as e:
                print(f"[AI] Connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)
```

---

*The full commented code for lan_chat.py will be added next. This file may be very large. Let me know if you want the full code with comments in a separate file or split into sections for easier reading!*
