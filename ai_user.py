import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lan_chat import random_nickname
import time
import random
import requests
import socketio
from dotenv import load_dotenv


load_dotenv()

print("[AI] Startup configuration:")
print(f"[AI]   API_TYPE: {os.getenv('AI_API_TYPE')}")
print(f"[AI]   API_URL:  {os.getenv('AI_API_URL')}")
print(f"[AI]   MODEL:    {os.getenv('AI_MODEL')}")
print(f"[AI]   SERVER:   {os.getenv('AI_SERVER_URL')}")

AI_API_TYPE = os.getenv("AI_API_TYPE", "ollama")
AI_API_URL = os.getenv("AI_API_URL", "http://10.107.101.37:11434/v1/chat/completions")
AI_MODEL = os.getenv("AI_MODEL", "qwen3:8b")
AI_NAME = random_nickname()
AI_FULL_NAME = os.getenv("AI_FULL_NAME", "LanAI Bot")
SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:5000")

sio = socketio.Client()

last_message_ts = None

@sio.event
def connect():
    print(f"[AI] Connected to chat server as {AI_NAME}")
    sio.emit("join", {"nickname": AI_NAME})
    # Do not send any initial response after login

@sio.event
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
def disconnect():
    print("[AI] Disconnected from chat server.")

def generate_reply(prompt):
    if AI_API_TYPE == "lmstudio":
        prompt_limited = f"{prompt}\nAnswer concisely and directly. Only provide the answer, no extra commentary."
        payload = {
            "model": AI_MODEL,
            "messages": [{"role": "user", "content": prompt_limited}],
            "temperature": 0.2
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
