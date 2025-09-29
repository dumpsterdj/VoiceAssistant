# # voice_assistant/wake.py
# import re
# import time
# import threading
# import webbrowser
#
# import speech_recognition as sr
#
# from . import config, tts, logger
# from .nlp_engine import NLPEngine
# from .commands import run_command, run_raw_command
# from .youtube_utils import yt_search_top_url, yt_download
#
# class WakeAssistant:
#     def __init__(self, wake_regex: str, allow_download=False, allow_arbitrary=False, openweather_key=None, voice_profile=None):
#         self.recognizer = sr.Recognizer()
#         try:
#             self.mic = sr.Microphone()
#             self.device_index = getattr(self.mic, "device_index", None)
#         except Exception as e:
#             print("Microphone error:", e)
#             raise
#         self.wake_re = re.compile(wake_regex, flags=re.IGNORECASE)
#         self.background_listener = None
#         self.running = False
#         self.busy_lock = threading.Lock()
#         self.allow_download = allow_download
#         self.allow_arbitrary = allow_arbitrary
#         self.openweather_key = openweather_key
#         self.voice_profile = voice_profile
#
#         # NLP instance
#         self.nlp = NLPEngine()
#
#     def start(self):
#         self.running = True
#         self.background_listener = self.recognizer.listen_in_background(self.mic, self._bg_callback, phrase_time_limit=4)
#         warn = "WARNING: downloads enabled." if self.allow_download else ""
#         arb = "ARBITRARY commands enabled." if self.allow_arbitrary else "Arbitrary commands disabled."
#         tts.speak(f"Assistant listening for wake phrase. {warn} {arb}")
#         try:
#             while self.running:
#                 time.sleep(0.5)
#         except KeyboardInterrupt:
#             self.stop()
#
#     def stop(self):
#         self.running = False
#         if self.background_listener:
#             self.background_listener(wait_for_stop=False)
#         tts.speak("Shutting down assistant.")
#         time.sleep(0.5)
#
#     def _bg_callback(self, recognizer, audio):
#         try:
#             txt = recognizer.recognize_google(audio)
#             print("[bg] Heard:", txt)
#         except sr.UnknownValueError:
#             return
#         except sr.RequestError as e:
#             print("Speech recognition service error (bg):", e)
#             return
#         if self.wake_re.search(txt):
#             tts.speak("Wake word detected.")
#             if self.busy_lock.locked():
#                 tts.speak("I'm busy. Try again shortly.")
#                 return
#             threading.Thread(target=self._handle, daemon=True).start()
#
#     # small helper to ask for a voice response (timeout seconds)
#     def _listen_for_reply(self, timeout=10, phrase_time_limit=10):
#         with sr.Microphone(device_index=self.device_index) as src:
#             self.recognizer.adjust_for_ambient_noise(src, duration=0.25)
#             try:
#                 audio = self.recognizer.listen(src, timeout=timeout, phrase_time_limit=phrase_time_limit)
#                 return audio
#             except sr.WaitTimeoutError:
#                 return None
#
#     def _recognize_audio(self, audio):
#         try:
#             return self.recognizer.recognize_google(audio)
#         except sr.UnknownValueError:
#             return None
#         except sr.RequestError as e:
#             print("Recognition error:", e)
#             return None
#
#     def _handle(self):
#         if not self.busy_lock.acquire(blocking=False):
#             return
#         try:
#             tts.speak("Yes?")
#             audio = self._listen_for_reply(timeout=6, phrase_time_limit=10)
#             if not audio:
#                 tts.speak("I didn't hear a command. Going back to sleep.")
#                 return
#             utter = self._recognize_audio(audio)
#             if not utter:
#                 tts.speak("Sorry, I didn't catch that.")
#                 return
#             print("[command] Recognized:", utter)
#             tts.speak(f"I heard: {utter}")
#
#             # map to intent/command
#             mapped = self._map_intent_or_command(utter)
#             if mapped[0] is None:
#                 reason = mapped[1]
#                 tts.speak(f"Couldn't map that: {reason}")
#                 if not self.allow_arbitrary:
#                     tts.speak("If you want arbitrary commands, restart with --allow-arbitrary.")
#                     return
#                 tts.speak(f"Do you want me to run the exact command: {utter}? Say 'run command' to confirm or 'cancel'.")
#                 audio2 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
#                 reply = self._recognize_audio(audio2) if audio2 else ""
#                 reply = (reply or "").lower()
#                 if reply not in ("run command", "run", "execute"):
#                     tts.speak("Cancelled.")
#                     logger.log_arbitrary(utter, confirmed=False, note="user declined")
#                     return
#                 # optional voice authentication would go here
#                 rc, out, err = run_raw_command(utter)
#                 logger.log_arbitrary(utter, confirmed=True, rc=rc, stdout=out, stderr=err)
#                 if rc == 0:
#                     tts.speak("Command executed successfully.")
#                     if out:
#                         tts.speak(out[:300])
#                 else:
#                     tts.speak("There was an error running that command.")
#                     if err:
#                         tts.speak(err[:200])
#                 return
#
#             base_cmd, args = mapped
#
#             # handle higher-level commands: weather, youtube play/download, web search
#             if base_cmd == "__weather__":
#                 city = args[0] if args else None
#                 if not city:
#                     tts.speak("Which city do you want the weather for?")
#                     audio2 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
#                     city = self._recognize_audio(audio2) if audio2 else None
#                 if not city:
#                     tts.speak("No city provided. Cancelling weather lookup.")
#                     return
#                 # lazy import to avoid cyclic deps
#                 from .main import get_weather
#                 ok, msg = get_weather(city, api_key=self.openweather_key)
#                 if ok:
#                     tts.speak(msg)
#                     logger.log_command(utter, "WEATHER", "weather", [city], 0, msg, "")
#                 else:
#                     tts.speak(msg)
#                     logger.log_command(utter, "WEATHER", "weather", [city], -1, "", msg)
#                 return
#
#             if base_cmd == "__youtube_play__":
#                 query = args[0]
#                 tts.speak(f"Searching YouTube for {query}")
#                 url = yt_search_top_url(query)
#                 tts.speak("Opening the top result in your browser.")
#                 webbrowser.open(url)
#                 logger.log_command(utter, "YOUTUBE_PLAY", "youtube_play", [query], 0, url, "")
#                 return
#
#             if base_cmd == "__youtube_download__":
#                 user_phrase = args[0] if args else ""
#                 query = self._clean_download_query(user_phrase)
#                 is_url = bool(re.match(r'https?://', query))
#                 yt_target = query if is_url else f"ytsearch1:{query}"
#
#                 if not self.allow_download:
#                     tts.speak("Downloads are disabled. Start assistant with --allow-download to enable.")
#                     logger.log_download(user_phrase, query, "", -1, "downloads_disabled")
#                     return
#
#                 tts.speak(f"You asked to download: {query}. Say 'download this' to confirm, or 'cancel'.")
#                 audio2 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
#                 reply = self._recognize_audio(audio2) if audio2 else ""
#                 reply = (reply or "").lower()
#                 if reply not in ("download this", "download", "yes download", "confirm"):
#                     tts.speak("Download cancelled.")
#                     logger.log_download(user_phrase, query, "", -1, "user_cancelled")
#                     return
#
#                 # if voice auth configured, verify here (omitted in modular split; you can add)
#                 tts.speak("Starting download. This may take some time.")
#                 rc, fname, err = yt_download(yt_target, dest_folder=".")
#                 logger.log_download(user_phrase, query, fname or "", rc, err or "")
#                 if rc == 0:
#                     tts.speak(f"Download finished. Saved as {fname and fname.split(os.sep)[-1]}")
#                 else:
#                     tts.speak(f"Download failed: {err}")
#                 return
#
#             if base_cmd == "__web_search__":
#                 q = args[0]
#                 tts.speak(f"Searching web for {q}")
#                 url = f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}"
#                 webbrowser.open(url)
#                 logger.log_command(utter, "WEB_SEARCH", "web_search", [q], 0, url, "")
#                 return
#
#             # sanitize and run whitelisted commands
#             success, reason = self._sanitize_and_validate(base_cmd, args)
#             if not success:
#                 tts.speak(reason)
#                 return
#             rc, out, err = run_command(base_cmd, args)
#             logger.log_command(utter, "WHITELIST", base_cmd, args, rc, out, err)
#             if rc == 0:
#                 if out:
#                     tts.speak(out[:300])
#                 else:
#                     tts.speak("Command completed successfully.")
#             else:
#                 tts.speak("Command error.")
#                 if err:
#                     tts.speak(err[:200])
#
#         finally:
#             if self.busy_lock.locked():
#                 self.busy_lock.release()
#
#     # helper functions (portions of old code)
#     def _map_intent_or_command(self, utterance: str):
#         """Map text -> (command, args) or (None, reason)."""
#         if not utterance or not utterance.strip():
#             return None, "No speech detected."
#         if re.search(r'\b(exit|quit|stop|shutdown assistant)\b', utterance.lower()):
#             return ("EXIT", [])
#
#         low = utterance.lower()
#         if "download" in low and ("youtube" in low or "video" in low):
#             return ("__youtube_download__", [utterance.strip()])
#
#         intent, score, best = self.nlp.predict_intent(utterance)
#         if not intent:
#             # try raw split for whitelisted commands
#             try:
#                 import shlex
#                 tokens = shlex.split(utterance.lower())
#                 if tokens and tokens[0] in config.ALLOWED_COMMANDS:
#                     return (tokens[0], tokens[1:])
#             except Exception:
#                 pass
#             return None, f"No intent match (best score {score} for '{best}')."
#
#         info = self.nlp.intents[intent]
#         cmd = info["cmd"]
#         slots = self.nlp.extract_slot(intent, utterance)
#
#         if cmd in config.ALLOWED_COMMANDS:
#             if cmd == "ipconfig":
#                 return ("ipconfig", [])
#             if cmd == "systeminfo":
#                 return ("systeminfo", [])
#             if cmd == "whoami":
#                 return ("whoami", [])
#             if cmd == "tasklist":
#                 return ("tasklist", [])
#             if cmd == "calc":
#                 return ("calc", [])
#             if cmd == "lock":
#                 return ("lock", [])
#             if cmd == "music":
#                 return ("music", [])
#             if cmd == "ping":
#                 target = slots.get("target") or "8.8.8.8"
#                 if any(ch in config.FORBIDDEN_CHARS for ch in target):
#                     return None, "Illegal characters in ping target."
#                 return ("ping", ["-n", "1", target.replace(' ', '.')])
#             if cmd == "tracert":
#                 target = slots.get("target")
#                 if not target:
#                     return ("tracert", [])
#                 return ("tracert", [target.replace(' ', '.')])
#             if cmd == "nslookup":
#                 target = slots.get("target")
#                 if not target:
#                     return ("nslookup", [])
#                 return ("nslookup", [target.replace(' ', '.')])
#
#         if cmd == "weather":
#             city = slots.get("city") or re.sub(r".* in ", "", utterance, flags=re.IGNORECASE).strip()
#             return ("__weather__", [city])
#         if cmd == "youtube_play":
#             q = None
#             if "play " in utterance.lower():
#                 q = re.sub(r"(?i)play\s+", "", utterance, count=1).strip()
#                 q = re.sub(r"(?i)\s+on youtube$", "", q).strip()
#             q = q or slots.get("query") or utterance
#             return ("__youtube_play__", [q])
#         if cmd == "youtube_download":
#             q = utterance.strip()
#             return ("__youtube_download__", [q])
#         if cmd == "web_search":
#             q = None
#             if "search " in utterance.lower():
#                 q = re.sub(r"(?i)search (?:web |google |for )?", "", utterance, count=1).strip()
#             q = q or slots.get("query") or utterance
#             return ("__web_search__", [q])
#
#         return None, "Intent recognized but no mapping available."
#
#     def _sanitize_and_validate(self, base, args):
#         if base not in config.ALLOWED_COMMANDS and not base.startswith("__"):
#             return False, f"Command '{base}' not allowed."
#         if base in config.ALLOWED_COMMANDS:
#             if not config.ALLOWED_COMMANDS[base]["accepts_args"] and args:
#                 return False, f"Command '{base}' does not accept arguments."
#             if " ".join(args) and len(" ".join(args)) > config.MAX_ARGS_LEN:
#                 return False, "Arguments too long."
#             if any(ch in config.FORBIDDEN_CHARS for ch in " ".join(args)):
#                 return False, "Illegal characters in arguments."
#         return True, None
#
#     def _clean_download_query(self, utterance: str) -> str:
#         u = utterance.lower().strip()
#         u = re.sub(r'\b(download( the video| the| this)?)\b', ' ', u)
#         u = re.sub(r'\bfrom youtube\b', ' ', u)
#         u = re.sub(r'\bon youtube\b', ' ', u)
#         u = re.sub(r'\bplease\b', ' ', u)
#         u = re.sub(r'[^A-Za-z0-9 \-._]', ' ', u)
#         u = re.sub(r'\s+', ' ', u).strip()
#         return u or utterance.strip()


# voice_assistant/wake.py
"""
Wake assistant with explicit spoken feedback for every major action.
Replace your existing voice_assistant/wake.py with this file.
"""

import os
import re
import time
import threading
import webbrowser
import shlex
from typing import Optional

import requests
import speech_recognition as sr

from . import config, tts, logger
from .nlp_engine import NLPEngine
from .commands import run_command, run_raw_command
from .youtube_utils import yt_search_top_url, yt_download


class WakeAssistant:
    def __init__(
        self,
        wake_regex: str,
        allow_download: bool = False,
        allow_arbitrary: bool = False,
        openweather_key: Optional[str] = None,
        voice_profile: Optional[str] = None,
    ):
        self.recognizer = sr.Recognizer()
        try:
            self.mic = sr.Microphone()
            self.device_index = getattr(self.mic, "device_index", None)
        except Exception as e:
            print("Microphone error:", e)
            raise
        self.wake_re = re.compile(wake_regex, flags=re.IGNORECASE)
        self.background_listener = None
        self.running = False
        self.busy_lock = threading.Lock()
        self.allow_download = allow_download
        self.allow_arbitrary = allow_arbitrary
        self.openweather_key = openweather_key
        self.voice_profile = voice_profile

        # NLP instance
        self.nlp = NLPEngine()

    # ----------------- lifecycle -----------------
    def start(self):
        """Start background listening and announce status."""
        self.running = True
        self.background_listener = self.recognizer.listen_in_background(
            self.mic, self._bg_callback, phrase_time_limit=4
        )
        warn = "Downloads enabled." if self.allow_download else "Downloads disabled."
        arb = "Arbitrary commands enabled." if self.allow_arbitrary else "Arbitrary commands disabled."
        tts.speak(f"Assistant ready. {warn} {arb}")
        print("Assistant started. Listening for wake phrase...")
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop background listener and announce shutdown."""
        self.running = False
        if self.background_listener:
            self.background_listener(wait_for_stop=False)
        tts.speak("Shutting down. Goodbye.")
        print("Assistant stopped.")

    # ----------------- background callback -----------------
    def _bg_callback(self, recognizer, audio):
        """Called in background when audio segment captured."""
        try:
            txt = recognizer.recognize_google(audio)
            print("[bg] Heard:", txt)
            # speak a short acknowledgement but avoid speaking too frequently:
            tts.speak("I heard something.")
        except sr.UnknownValueError:
            # don't speak when nothing understandable
            return
        except sr.RequestError as e:
            print("Speech recognition service error (bg):", e)
            tts.speak("Background speech recognition service error.")
            return

        if self.wake_re.search(txt):
            tts.speak("Wake word detected.")
            print("Wake word matched.")
            if self.busy_lock.locked():
                tts.speak("I'm busy, please try again shortly.")
                return
            # start handling in a separate thread
            threading.Thread(target=self._handle, daemon=True).start()

    # ----------------- helpers for listening & recognition -----------------
    def _listen_for_reply(self, timeout=10, phrase_time_limit=10):
        """Listen and return audio object or None; announce start/stop of listening."""
        try:
            tts.speak("Listening now.")
            with sr.Microphone(device_index=self.device_index) as src:
                # adapt to ambient noise briefly
                self.recognizer.adjust_for_ambient_noise(src, duration=0.25)
                try:
                    audio = self.recognizer.listen(src, timeout=timeout, phrase_time_limit=phrase_time_limit)
                    tts.speak("Got your response.")
                    return audio
                except sr.WaitTimeoutError:
                    tts.speak("I didn't hear anything.")
                    return None
        except Exception as e:
            print("Microphone/listen error:", e)
            tts.speak("Microphone error while listening.")
            return None

    def _recognize_audio(self, audio) -> Optional[str]:
        """Recognize audio using Google API; announce errors."""
        if not audio:
            return None
        try:
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            tts.speak("Sorry, I couldn't understand.")
            return None
        except sr.RequestError as e:
            print("Recognition error:", e)
            tts.speak("Speech recognition service error.")
            return None

    # ----------------- main handler -----------------
    def _handle(self):
        """Handles a single wake-and-command interaction with spoken feedback."""
        if not self.busy_lock.acquire(blocking=False):
            return
        try:
            tts.speak("Yes?")
            audio = self._listen_for_reply(timeout=6, phrase_time_limit=10)
            if not audio:
                # already announced in _listen_for_reply
                return

            utter = self._recognize_audio(audio)
            if not utter:
                # error already announced by _recognize_audio
                return

            print("[command] Recognized:", utter)
            tts.speak(f"I heard: {utter}")

            # map the utterance to an intent/command
            mapped = self._map_intent_or_command(utter)
            if mapped[0] is None:
                # no mapping
                reason = mapped[1]
                tts.speak(f"I couldn't map that. {reason}")
                print("Mapping failed:", reason)

                if not self.allow_arbitrary:
                    tts.speak("Arbitrary commands are disabled. To allow them restart with allow-arbitrary.")
                    return

                # ask for confirmation to run exact text
                tts.speak(f"Do you want me to run the exact command: {utter}? Say 'run command' to confirm.")
                audio2 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
                reply = self._recognize_audio(audio2) if audio2 else ""
                reply = (reply or "").lower()
                if reply not in ("run command", "run", "execute", "yes"):
                    tts.speak("Cancelled by user.")
                    logger.log_arbitrary(utter, confirmed=False, note="user declined")
                    return

                tts.speak("Running your arbitrary command now.")
                rc, out, err = run_raw_command(utter)
                logger.log_arbitrary(utter, confirmed=True, rc=rc, stdout=out, stderr=err)
                if rc == 0:
                    tts.speak("Command completed successfully.")
                    if out:
                        tts.speak(out[:250])
                else:
                    tts.speak("There was an error running that command.")
                    if err:
                        tts.speak(err[:200])
                return

            base_cmd, args = mapped

            # --- HANDLE high-level intents ---
            if base_cmd == "__weather__":
                city = args[0] if args else None
                if not city:
                    tts.speak("Which city would you like the weather for?")
                    audio2 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
                    city = self._recognize_audio(audio2) if audio2 else None
                if not city:
                    tts.speak("No city provided. Cancelling weather lookup.")
                    return
                # lazy import to avoid circular imports
                from .main import get_weather
                ok, msg = get_weather(city, api_key=self.openweather_key)
                if ok:
                    tts.speak(msg)
                    logger.log_command(utter, "WEATHER", "weather", [city], 0, msg, "")
                else:
                    tts.speak(msg)
                    logger.log_command(utter, "WEATHER", "weather", [city], -1, "", msg)
                return

            if base_cmd == "__youtube_play__":
                query = args[0]
                tts.speak(f"Searching YouTube for {query}")
                url = yt_search_top_url(query)
                tts.speak("Opening top result in browser.")
                webbrowser.open(url)
                logger.log_command(utter, "YOUTUBE_PLAY", "youtube_play", [query], 0, url, "")
                return

            if base_cmd == "__youtube_download__":
                user_phrase = args[0] if args else ""
                query = self._clean_download_query(user_phrase)
                is_url = bool(re.match(r"https?://", query))
                yt_target = query if is_url else f"ytsearch1:{query}"

                if not self.allow_download:
                    tts.speak("Downloads are disabled. Restart with allow-download to enable.")
                    logger.log_download(user_phrase, query, "", -1, "downloads_disabled")
                    return

                tts.speak(f"You asked to download {query}. Say 'download this' to confirm.")
                audio2 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
                reply = self._recognize_audio(audio2) if audio2 else ""
                reply = (reply or "").lower()
                if reply not in ("download this", "download", "confirm", "yes"):
                    tts.speak("Download cancelled.")
                    logger.log_download(user_phrase, query, "", -1, "user_cancelled")
                    return

                tts.speak("Starting download. I will announce when it's finished or if it fails.")
                rc, fname, err = yt_download(yt_target, dest_folder=".")
                logger.log_download(user_phrase, query, fname or "", rc, err or "")
                if rc == 0:
                    shortname = fname.split(os.sep)[-1] if fname else "file"
                    tts.speak(f"Download finished. Saved as {shortname}")
                else:
                    tts.speak(f"Download failed: {err}")
                return

            if base_cmd == "__web_search__":
                q = args[0]
                tts.speak(f"Searching the web for {q}")
                url = f"https://www.google.com/search?q={requests.utils.requote_uri(q)}"
                webbrowser.open(url)
                logger.log_command(utter, "WEB_SEARCH", "web_search", [q], 0, url, "")
                return

            # --- WHITELISTED COMMANDS ---
            ok, reason = self._sanitize_and_validate(base_cmd, args)
            if not ok:
                tts.speak(reason)
                return

            # confirmation for network-related or potentially sensitive commands
            if args and base_cmd in ("ping", "tracert", "nslookup"):
                tts.speak(f"I will run {base_cmd} with { ' '.join(args) }. Say 'yes' to confirm.")
                audio3 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
                reply = self._recognize_audio(audio3) if audio3 else ""
                reply = (reply or "").lower()
                if reply not in ("yes", "confirm", "sure"):
                    tts.speak("Cancelled.")
                    return

            if base_cmd == "shutdown":
                tts.speak("This will shutdown your PC. Say 'yes' to confirm.")
                audio3 = self._listen_for_reply(timeout=10, phrase_time_limit=10)
                reply = self._recognize_audio(audio3) if audio3 else ""
                reply = (reply or "").lower()
                if reply not in ("yes", "confirm", "shutdown"):
                    tts.speak("Shutdown cancelled.")
                    return

            tts.speak(f"Running {base_cmd} now.")
            rc, out, err = run_command(base_cmd, args)
            logger.log_command(utter, "WHITELIST", base_cmd, args, rc, out, err)
            if rc == 0:
                if out:
                    # speak a short portion of output
                    tts.speak(out[:250])
                else:
                    tts.speak("Command completed successfully.")
            else:
                tts.speak("Command returned an error.")
                if err:
                    tts.speak(err[:200])

        finally:
            if self.busy_lock.locked():
                self.busy_lock.release()

    # ----------------- intent mapping & helpers (ported from previous code) -----------------
    def _map_intent_or_command(self, utterance: str):
        """Map text -> (command, args) or (None, reason)."""
        if not utterance or not utterance.strip():
            return None, "No speech detected."
        if re.search(r"\b(exit|quit|stop|shutdown assistant)\b", utterance.lower()):
            return ("EXIT", [])

        low = utterance.lower()
        if "download" in low and ("youtube" in low or "video" in low):
            return ("__youtube_download__", [utterance.strip()])

        intent, score, best = self.nlp.predict_intent(utterance)
        if not intent:
            # try raw split for whitelisted commands
            try:
                tokens = shlex.split(utterance.lower())
                if tokens and tokens[0] in config.ALLOWED_COMMANDS:
                    return (tokens[0], tokens[1:])
            except Exception:
                pass
            return None, f"No intent match (best score {score} for '{best}')."

        info = self.nlp.intents[intent]
        cmd = info["cmd"]
        slots = self.nlp.extract_slot(intent, utterance)

        if cmd in config.ALLOWED_COMMANDS:
            if cmd == "ipconfig":
                return ("ipconfig", [])
            if cmd == "systeminfo":
                return ("systeminfo", [])
            if cmd == "whoami":
                return ("whoami", [])
            if cmd == "tasklist":
                return ("tasklist", [])
            if cmd == "calc":
                return ("calc", [])
            if cmd == "lock":
                return ("lock", [])
            if cmd == "music":
                return ("music", [])
            if cmd == "ping":
                target = slots.get("target") or "8.8.8.8"
                if any(ch in config.FORBIDDEN_CHARS for ch in target):
                    return None, "Illegal characters in ping target."
                return ("ping", ["-n", "1", target.replace(" ", ".")])
            if cmd == "tracert":
                target = slots.get("target")
                if not target:
                    return ("tracert", [])
                return ("tracert", [target.replace(" ", ".")])
            if cmd == "nslookup":
                target = slots.get("target")
                if not target:
                    return ("nslookup", [])
                return ("nslookup", [target.replace(" ", ".")])

        if cmd == "weather":
            city = slots.get("city") or re.sub(r".* in ", "", utterance, flags=re.IGNORECASE).strip()
            return ("__weather__", [city])
        if cmd == "youtube_play":
            q = None
            if "play " in utterance.lower():
                q = re.sub(r"(?i)play\s+", "", utterance, count=1).strip()
                q = re.sub(r"(?i)\s+on youtube$", "", q).strip()
            q = q or slots.get("query") or utterance
            return ("__youtube_play__", [q])
        if cmd == "youtube_download":
            q = utterance.strip()
            return ("__youtube_download__", [q])
        if cmd == "web_search":
            q = None
            if "search " in utterance.lower():
                q = re.sub(r"(?i)search (?:web |google |for )?", "", utterance, count=1).strip()
            q = q or slots.get("query") or utterance
            return ("__web_search__", [q])

        return None, "Intent recognized but no mapping available."

    def _sanitize_and_validate(self, base, args):
        if base not in config.ALLOWED_COMMANDS and not base.startswith("__"):
            return False, f"Command '{base}' not allowed."
        if base in config.ALLOWED_COMMANDS:
            if not config.ALLOWED_COMMANDS[base]["accepts_args"] and args:
                return False, f"Command '{base}' does not accept arguments."
            if " ".join(args) and len(" ".join(args)) > config.MAX_ARGS_LEN:
                return False, "Arguments too long."
            if any(ch in config.FORBIDDEN_CHARS for ch in " ".join(args)):
                return False, "Illegal characters in arguments."
        return True, None

    def _clean_download_query(self, utterance: str) -> str:
        u = utterance.lower().strip()
        u = re.sub(r"\b(download( the video| the| this)?)\b", " ", u)
        u = re.sub(r"\bfrom youtube\b", " ", u)
        u = re.sub(r"\bon youtube\b", " ", u)
        u = re.sub(r"\bplease\b", " ", u)
        u = re.sub(r"[^A-Za-z0-9 \-._]", " ", u)
        u = re.sub(r"\s+", " ", u).strip()
        return u or utterance.strip()
