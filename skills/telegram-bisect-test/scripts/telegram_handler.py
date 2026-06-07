#!/usr/bin/env python3
"""
telegram_handler.py - Telegram bot handler for telegram-bisect-test

This script:
1. Runs a simple HTTP server that receives Telegram webhook updates
2. Parses incoming messages for GOOD/BAD responses
3. Updates session state based on the response
4. Sends follow-up messages via Telegram

Usage:
    python3 telegram_handler.py [--port 8080]

Requires: Python requests library for Telegram API calls
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Import configuration and session management
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SESSIONS_DIR, GOOD_KEYWORDS, BAD_KEYWORDS
from scripts.manage_sessions import load_session as ms_load_session, save_session as ms_save_session


def parse_reply_type(body: str) -> Optional[str]:
    """Parse a message body to determine if it's GOOD, BAD, or neither."""
    text = body.lower().strip()
    
    # Check for GOOD indicators
    for keyword in GOOD_KEYWORDS:
        if keyword in text:
            return "good"
    
    # Check for BAD indicators  
    for keyword in BAD_KEYWORDS:
        if keyword in text:
            return "bad"
    
    return None


def send_telegram_message(chat_id: str, text: str):
    """Send a message to Telegram."""
    import requests
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram API error: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


def load_session(session_id: str):
    """Load a bisect session JSON file."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return None
    try:
        with open(session_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_session(session_id: str, session_data: dict):
    """Save a bisect session JSON file."""
    ensure_sessions_dir()
    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)


def ensure_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


class TelegramHandler(BaseHTTPRequestHandler):
    """HTTP handler for Telegram webhook."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_POST(self):
        """Handle incoming Telegram webhook updates."""
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON
            update = json.loads(body)
            
            # Extract message if present
            if 'message' not in update:
                self.send_response(200)
                self.end_headers()
                return
            
            message = update['message']
            
            # Get sender info
            from_user = message.get('from', {})
            sender_username = from_user.get('username', 'unknown')
            
            # Get message text
            text = message.get('text', '')
            
            # Parse the response type
            reply_type = parse_reply_type(text)
            
            if not reply_type:
                # Not a valid response - send help message
                send_telegram_message(TELEGRAM_CHAT_ID, 
                    f"Please reply with **GOOD** or **BAD** to continue the test.\n\n"
                    f"*GOOD* - Item passes / issue not present\n"
                    f"*BAD*  - Item fails / issue present")
                self.send_response(200)
                self.end_headers()
                return
            
            # Find the active session for this user
            active_session = None
            for json_file in SESSIONS_DIR.glob("*.json"):
                session = load_session(json_file.stem)
                if session and session.get("reporter") == sender_username:
                    active_session = json_file.stem
                    break
            
            if not active_session:
                send_telegram_message(TELEGRAM_CHAT_ID,
                    f"No active session found for @{sender_username}.\n\n"
                    f"Start a new test with:\n"
                    f"`python3 manage-sessions.py start \"1..50\" {sender_username}`")
                self.send_response(200)
                self.end_headers()
                return
            
            # Load and update the session
            session = ms_load_session(active_session)
            
            if not session:
                send_telegram_message(TELEGRAM_CHAT_ID,
                    f"Error loading session {active_session}. Please restart the test.")
                self.send_response(200)
                self.end_headers()
                return
            
            if reply_type == "good":
                # Calculate next item (binary search - go right)
                range_start = session["range"]["start"]
                range_end = session["range"]["end"]
                
                if session.get("last_step"):
                    last_item = session["last_step"].get("item", range_start)
                    new_start = last_item + 1
                    new_end = range_end
                else:
                    new_start = (range_start + range_end) // 2
                
                if new_start <= range_end:
                    next_item = (new_start + range_end) // 2
                else:
                    next_item = None
                
                session["last_step"] = {
                    "step_number": (session.get("last_step", {}).get("step_number") or 0) + 1,
                    "item": next_item if next_item is not None else (range_start + range_end) // 2,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "result": "good"
                }
                
            else:  # bad
                range_start = session["range"]["start"]
                range_end = session["range"]["end"]
                
                if session.get("last_step"):
                    last_item = session["last_step"].get("item", range_end)
                    new_start = range_start
                    new_end = last_item - 1
                else:
                    new_end = (range_start + range_end) // 2
                
                if range_start <= new_end:
                    next_item = (range_start + new_end) // 2
                else:
                    next_item = None
                
                session["last_step"] = {
                    "step_number": (session.get("last_step", {}).get("step_number") or 0) + 1,
                    "item": next_item if next_item is not None else (range_start + range_end) // 2,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "result": "bad"
                }
            
            # Update status
            if next_item is None:
                session["status"] = "converged"
            else:
                session["status"] = "in_progress"
            
            ms_save_session(active_session, session)
            
            # Send response message
            if next_item is None:
                msg = (f"✅ **Test converged!**\n\n"
                       f"Final item tested: {session['last_step']['item']}\n"
                       f"Total steps: {session['last_step']['step_number']}")
            else:
                msg = (f"🔬 **Step {session['last_step']['step_number']}**\n\n"
                       f"Testing item **{next_item}**...\n\n"
                       f"*GOOD* - Item passes / issue not present\n"
                       f"*BAD*  - Item fails / issue present")
            
            send_telegram_message(TELEGRAM_CHAT_ID, msg)
            
        except Exception as e:
            print(f"Error handling webhook: {e}")
        
        self.send_response(200)
        self.end_headers()


def run_server(port: int = 8080):
    """Run the Telegram webhook server."""
    print(f"Starting Telegram handler on port {port}...")
    print(f"Set webhook URL to: https://your-domain.com:{port}/telegram/webhook")
    print("Press Ctrl+C to stop.")
    
    server = HTTPServer(('0.0.0.0', port), TelegramHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    run_server(port)
