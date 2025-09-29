# voice_assistant/tts.py
import pyttsx3
import threading

_engine = pyttsx3.init()
_engine.setProperty("rate", 160)
_lock = threading.Lock()

def speak(text: str):
    """Speak the given text (thread-safe)."""
    with _lock:
        print("[Assistant speaking]", text)
        try:
            _engine.say(text)
            _engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)
