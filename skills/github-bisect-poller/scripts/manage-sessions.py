#!/usr/bin/env python3
"""
manage-sessions.py - Session management for github-bisect-poller

Commands:
    list              List all active sessions
    create <issue> <reporter>  Create a new session for an issue
    advance <id> <result>      Advance a session (good|bad)
    show <id>         Show session details

Usage:
    python3 manage-sessions.py list
    python3 manage-sessions.py create 42 "bug-reporter"
    python3 manage-sessions.py advance abc123 good
    python3 manage-sessions.py show abc123
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Import configuration
from config import GITHUB_REPO, SESSIONS_DIR


def ensure_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def list_sessions():
    """List all active sessions."""
    if not SESSIONS_DIR.exists():
        print("No sessions directory found.")
        return
    
    for json_file in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            with open(json_file) as f:
                session = json.load(f)
            
            status = session.get("status", "unknown")
            issue_num = session.get("issue_number", "?")
            reporter = session.get("reporter", "unknown")
            
            print(f"{json_file.stem}: Issue #{issue_num} - {reporter} [{status}]")
        except (json.JSONDecodeError, IOError) as e:
            print(f"{json_file.stem}: Error - {e}")


def create_session(issue_number: int, reporter_username: str):
    """Create a new session for an issue."""
    ensure_sessions_dir()
    
    # Generate a unique session ID
    session_id = f"{issue_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    session = {
        "session_id": session_id,
        "issue_number": issue_number,
        "reporter": reporter_username,
        "status": "in_progress",
        "last_step": None,
        "notes": ""
    }
    
    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    
    print(f"Created session {session_id} for issue #{issue_number}")


def advance_session(session_id: str, result: str):
    """Advance a session based on reporter response."""
    if result not in ("good", "bad"):
        print(f"Invalid result type: {result}. Must be 'good' or 'bad'.")
        return
    
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        print(f"Session {session_id} not found.")
        return
    
    try:
        with open(session_file) as f:
            session = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading session {session_id}: {e}")
        return
    
    # Update last step with current timestamp
    session["last_step"] = {
        "step_number": (session.get("last_step", {}).get("step_number") or 0) + 1,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "result": result
    }
    
    # Update status based on result
    if result == "good" or result == "bad":
        session["status"] = "converged" if session.get("last_step", {}).get("step_number") == 1 else "in_progress"
    
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    
    print(f"Advanced session {session_id} to step {session['last_step']['step_number']} ({result})")


def show_session(session_id: str):
    """Show session details."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        print(f"Session {session_id} not found.")
        return
    
    try:
        with open(session_file) as f:
            session = json.load(f)
        
        print(json.dumps(session, indent=2))
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading session {session_id}: {e}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_sessions()
    
    elif command == "create" and len(sys.argv) >= 4:
        create_session(int(sys.argv[2]), sys.argv[3])
    
    elif command == "advance" and len(sys.argv) >= 4:
        advance_session(sys.argv[2], sys.argv[3])
    
    elif command == "show" and len(sys.argv) >= 3:
        show_session(sys.argv[2])
    
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
