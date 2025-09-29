# 🎙️ VoiceAssistant — "Hey DJ"

A **local-first voice assistant for Windows** with wake-word support ("hey DJ"), natural-language intent mapping, safe system command execution, YouTube helpers, and text-to-speech feedback.

---

## ✨ Features

- 🔊 **Wake word detection** — say *"hey DJ"* to activate.
- 🧠 **Lightweight NLP engine** — maps natural phrases (e.g., *"show my IP"*) to commands.
- 🖥️ **Whitelisted system commands** — `ping`, `ipconfig`, `systeminfo`, etc.  
  ↳ with confirmation prompts for sensitive actions like shutdown.
- 📺 **YouTube play & download** via `yt-dlp` (requires `--allow-download`).
- 📢 **TTS feedback** using `pyttsx3` so you always get audible responses.
- 🌦️ **Weather lookup** via OpenWeatherMap API.
- 📝 **Logging** of all commands, downloads, and arbitrary actions.

---

## 🚀 Quick Start

### 1. Clone the repository
```powershell
git clone https://github.com/dumpsterdj/VoiceAssistant.git
cd VoiceAssistant
````

### 2. Setup environment

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

> ⚠️ Some optional dependencies (`PyAudio`, `webrtcvad`) require Microsoft C++ Build Tools. See docs for setup.

### 3. Run the assistant

```powershell
python -m VoiceAssistant.main --allow-download --allow-arbitrary
```

---

## 🎤 Usage

* Wake the assistant by saying:
  **“hey DJ”**
* Example commands:

  * *"show my IP"* → runs `ipconfig`
  * *"ping google.com"* → runs `ping`
  * *"what’s the weather in London"* → fetches weather
  * *"play despacito on YouTube"* → opens top result
  * *"download this video"* → prompts before downloading

---

## 🛡️ Security

* ⚠️ **Arbitrary command execution** is disabled by default. Use `--allow-arbitrary` only in trusted environments.
* ⚠️ **Downloads** require `--allow-download` *and* a spoken confirmation.
* Voice profiles (if enabled) are stored locally only. Protect the `voice_profiles/` folder.

---

## 📂 Project Structure

```
VoiceAssistant/
├─ .venv/                     # Virtual environment
├─ __init__.py                 # Marks this folder as a package
├─ commands.py                 # Command execution logic
├─ config.py                   # Configuration and constants
├─ logger.py                   # Logging utilities
├─ main.py                     # Entry point
├─ nlp_engine.py               # Lightweight NLP intent engine
├─ requirements.txt            # Python dependencies
├─ start_voice_assistant.bat   # Windows startup batch file
├─ tts.py                      # Text-to-speech functions
├─ wake.py                     # Wake-word and voice control
└─ youtube_utils.py            # YouTube play/download helpers
```

---

## 🧪 Development

### Run tests

```bash
pytest -q
```

### Lint with flake8

```bash
flake8 voice_assistant
```

---

## 🤝 Contributing

Contributions welcome!

* Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.
* Please open issues for bugs, suggestions, or feature requests.

---

## 📜 License

MIT License © 2025 dumpsterdj
See [LICENSE](LICENSE) for details.
```
