# voice_assistant/config.py
import os

# Wake word patterns (regular expressions)
WAKE_PATTERNS = [r'\bhey dj\b', r'\bhey dee jay\b', r'\bhey d\.j\.\b', r'\bhello d\.j\.\b', r'\bhey dj assistant\b']
WAKE_WORDS = "(" + "|".join(WAKE_PATTERNS) + ")"

# Allowed CLI commands (whitelist)
ALLOWED_COMMANDS = {
    "ipconfig": {"accepts_args": True},
    "ping": {"accepts_args": True},
    "tracert": {"accepts_args": True},
    "nslookup": {"accepts_args": True},
    "systeminfo": {"accepts_args": False},
    "whoami": {"accepts_args": False},
    "tasklist": {"accepts_args": False},
    "calc": {"accepts_args": False},
    "shutdown": {"accepts_args": True},
    "lock": {"accepts_args": False},
    "music": {"accepts_args": False},
}

MAX_ARGS_LEN = 120
FORBIDDEN_CHARS = set("&|;><$`")

# Logging filenames
COMMANDS_LOG = "commands.log"
DOWNLOADS_LOG = "downloads.log"
ARBITRARY_LOG = "arbitrary_commands.log"

# External API keys (optional; can be passed as env var or CLI arg)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", None)
