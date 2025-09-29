# voice_assistant/main.py
import argparse
import webbrowser
import requests
from .config import WAKE_WORDS
from .wake import WakeAssistant
from . import logger, tts

def get_weather(city: str, api_key: str = None):
    key = api_key
    if not key:
        return False, "OpenWeatherMap API key not set. Set OPENWEATHER_API_KEY env var or pass --openweather-key."
    url = f"http://api.openweathermap.org/data/2.5/weather?q={requests.utils.requote_uri(city)}&appid={key}&units=metric"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return False, f"Weather API error: {r.status_code} {r.text[:200]}"
        j = r.json()
        name = j.get("name")
        main = j.get("weather", [{}])[0].get("main", "")
        desc = j.get("weather", [{}])[0].get("description", "")
        temp = j.get("main", {}).get("temp")
        feels = j.get("main", {}).get("feels_like")
        humidity = j.get("main", {}).get("humidity")
        return True, f"{name}: {main} ({desc}). Temperature {temp}°C, feels like {feels}°C. Humidity {humidity}%."
    except Exception as ex:
        return False, f"Weather lookup failed: {ex}"

def parse_args():
    p = argparse.ArgumentParser(description="Wake-word assistant (Hey DJ)")
    p.add_argument("--allow-download", action="store_true", help="Allow YouTube downloads (requires spoken confirmation per-download).")
    p.add_argument("--allow-arbitrary", action="store_true", help="Allow arbitrary command execution.")
    p.add_argument("--openweather-key", default=None, help="OpenWeatherMap API key or set OPENWEATHER_API_KEY env var.")
    p.add_argument("--voice-profile", default=None, help="(optional) voice profile name (if voice auth integrated)")
    return p.parse_args()

def main():
    args = parse_args()
    if args.allow_download:
        print("Downloads are ENABLED for this session. Use responsibly.")
    if args.allow_arbitrary:
        print("Arbitrary commands ENABLED.")
    if args.voice_profile:
        print("Voice profile configured:", args.voice_profile)

    try:
        assistant = WakeAssistant(WAKE_WORDS, allow_download=args.allow_download, allow_arbitrary=args.allow_arbitrary, openweather_key=args.openweather_key, voice_profile=args.voice_profile)
    except Exception as e:
        print("Failed to init microphone:", e)
        tts.speak("Microphone initialization failed.")
        return
    assistant.start()

if __name__ == "__main__":
    main()
