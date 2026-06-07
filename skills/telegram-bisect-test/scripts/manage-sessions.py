#!/usr/bin/env python3
"""
manage-sessions.py - Session management for telegram-bisect-test

Commands:
    start <range> [reporter]  Start a new session (e.g., "1..50")
    status <id>               Show session details and current state
    advance <id> <result>     Advance a session (good|bad)
    close <id>                Close a completed session

Usage:
    python3 manage-sessions.py start "1..50" your-username
    python3 manage-sessions.py status abc123
    python3 manage-sessions.py advance abc123 good
    python3 manage-sessions.py close abc123
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Import configuration - edit this file to customize for your workflow
from config import SESSIONS_DIR, GOOD_KEYWORDS, BAD_KEYWORDS


def ensure_sessions_dir():
    """Create sessions directory if it doesn't exist."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def parse_range(range_str: str):
    """Parse a range string like '1..50' into (start, end) tuple."""
    parts = range_str.split("..")
    if len(parts) != 2:
        raise ValueError(f"Invalid range format: {range_str}. Use 'start..end'")
    return int(parts[0]), int(parts[1])


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
            reporter = session.get("reporter", "unknown")
            
            print(f"{json_file.stem}: {reporter} [{status}]")
        except (json.JSONDecodeError, IOError) as e:
            print(f"{json_file.stem}: Error - {e}")


def start_session(range_str: str, reporter_username: str):
    """Create a new session."""
    ensure_sessions_dir()
    
    try:
        start, end = parse_range(range_str)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Generate a unique session ID
    session_id = f"tg-bisect-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    session = {
        "session_id": session_id,
        "reporter": reporter_username,
        "status": "in_progress",
        "range": {"start": start, "end": end},
        "last_step": None,
        "notes": ""
    }
    
    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    
    print(f"Created session {session_id}")
    print(f"  Range: {start}..{end}")
    print(f"  Reporter: {reporter_username}")
    print(f"  Max steps (log2): ~{int(__import__('math').log2(end - start + 1))}")


def status_session(session_id: str):
    """Show session details and current state."""
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


def advance_session(session_id: str, result: str):
    """Advance a session based on response."""
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
    
    # Calculate next step using binary search logic
    range_start = session["range"]["start"]
    range_end = session["range"]["end"]
    
    # Get current midpoint or calculate new one
    if session.get("last_step"):
        last_item = session["last_step"].get("item")
        if last_item:
            # Continue binary search from current position
            if result == "good":
                new_start = last_item + 1
                new_end = range_end
            else:
                new_start = range_start
                new_end = last_item - 1
            
            # Calculate midpoint of new range
            if new_start <= new_end:
                next_item = (new_start + new_end) // 2
            else:
                # Converged - no more items to test
                next_item = None
        else:
            # First step after start
            if result == "good":
                next_item = (range_start + range_end) // 2
            else:
                next_item = None
    else:
        # First step - midpoint of full range
        next_item = (range_start + range_end) // 2
    
    # Update last step
    session["last_step"] = {
        "step_number": (session.get("last_step", {}).get("step_number") or 0) + 1,
        "item": next_item if next_item is not None else (range_start + range_end) // 2,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "result": result
    }
    
    # Update status based on convergence
    if next_item is None:
        session["status"] = "converged"
    else:
        session["status"] = "in_progress"
    
    with open(session_file, "w") as f:
        json.dump(session, f, indent=2)
    
    if next_item is None:
        print(f"Session {session_id} converged after step {session['last_step']['step_number']}")
    else:
        print(f"Advanced session {session_id} to item {next_item} (step {session['last_step']['step_number']})")


def close_session(session_id: str):
    """Close a completed session."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        print(f"Session {session_id} not found.")
        return
    
    try:
        with open(session_file) as f:
            session = json.load(f)
        
        # Update status to closed
        session["status"] = "closed"
        session["closed_at"] = datetime.utcnow().isoformat() + "Z"
        
        with open(session_file, "w") as f:
            json.dump(session, f, indent=2)
        
        print(f"Closed session {session_id}")
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error closing session {session_id}: {e}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "start" and len(sys.argv) >= 3:
        range_str = sys.argv[2]
        reporter = sys.argv[3] if len(sys.argv) > 3 else "unknown"
        start_session(range_str, reporter)
    
    elif command == "status" and len(sys.argv) >= 3:
        status_session(sys.argv[2])
    
    elif command == "advance" and len(sys.argv) >= 4:
        advance_session(sys.argv[2], sys.argv[3])
    
    elif command == "close" and len(sys.argv) >= 3:
        close_session(sys.argv[2])
    
    elif command == "list":
        list_sessions()
    
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
