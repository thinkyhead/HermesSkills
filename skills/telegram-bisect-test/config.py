#!/usr/bin/env python3
"""
Configuration for telegram-bisect-test

Edit these values to adapt the test workflow to your setup.
"""

from pathlib import Path

# Telegram bot configuration - get token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = "your-bot-token-here"

# Your Telegram chat ID (or group ID if testing in a group)
TELEGRAM_CHAT_ID = "your-chat-id-here"

# Directory where session JSON files are stored
SESSIONS_DIR = Path.home() / ".hermes/telegram-bisect-sessions"

# Keywords that indicate a positive response
GOOD_KEYWORDS = {
    "good", "pass", "works", "ok", "accepted", 
    "yes", "approved", "confirmed"
}

# Keywords that indicate a negative response
BAD_KEYWORDS = {
    "bad", "fail", "broken", "rejected", "not ok", 
    "no", "declined", "unconfirmed"
}

# How many items to test per session (default: 50)
DEFAULT_RANGE_SIZE = 50
