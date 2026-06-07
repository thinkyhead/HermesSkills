#!/usr/bin/env python3
"""
poll-bisect-replies.py - Poll GitHub issues for reporter responses

This script:
1. Lists all active bisect sessions from SESSIONS_DIR
2. For each session, fetches recent GitHub issue comments
3. Parses for clear GOOD/BAD replies from the reporter (not Hermes or other maintainers)
4. Reports findings: either session details with response type, or "[SILENT]" if no updates

Usage:
    python3 poll-bisect-replies.py [--verbose]

Output format for cron jobs:
    - If new replies found: Reports session details with response type
    - If no updates: [SILENT] (nothing else)

Requires: gh CLI installed and authenticated
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# Import configuration - edit this file to customize for your workflow
from config import (
    GITHUB_REPO, SESSIONS_DIR, GOOD_KEYWORDS, BAD_KEYWORDS, MAX_COMMENTS_TO_CHECK
)


def run_gh_command(args: List[str]) -> Optional[str]:
    """Run a gh CLI command and return stdout, or None on error."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error running gh: {e}", file=sys.stderr)
        return None


def load_session(session_id: str) -> Optional[Dict]:
    """Load a bisect session JSON file."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return None
    try:
        with open(session_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading session {session_id}: {e}", file=sys.stderr)
        return None


def get_issue_comments(issue_number: int) -> Optional[List[Dict]]:
    """Fetch all comments for a GitHub issue using gh CLI."""
    jq_filter = '.comments[] | {login: .author.login, createdAt: .createdAt, body: .body}'
    args = [
        "issue", "view", str(issue_number),
        "--repo", GITHUB_REPO,
        "--comments",
        "--jq", jq_filter
    ]
    output = run_gh_command(args)
    if not output:
        return None
    
    try:
        comments = json.loads(output)
        # Sort by date descending (newest first)
        return sorted(comments, key=lambda c: c.get("createdAt", ""), reverse=True)[:MAX_COMMENTS_TO_CHECK]
    except json.JSONDecodeError as e:
        print(f"Error parsing comments JSON: {e}", file=sys.stderr)
        return None


def parse_reply_type(body: str) -> Optional[str]:
    """Parse a comment body to determine if it's GOOD, BAD, or neither."""
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


def check_session(session_id: str, verbose: bool = False) -> Optional[Dict]:
    """Check a single bisect session for new replies."""
    session = load_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    
    # Skip non-active sessions
    if session.get("status") != "in_progress":
        return None
    
    issue_number = session.get("issue_number")
    reporter_username = session.get("reporter")
    
    if not issue_number or not reporter_username:
        return {"error": f"Session {session_id} missing required fields"}
    
    # Fetch recent comments (last N should be enough)
    comments = get_issue_comments(issue_number)
    if not comments:
        return {"error": "Failed to fetch issue comments"}
    
    # Find the reporter's most recent comment that contains GOOD/BAD
    for comment in comments:
        if comment.get("login") != reporter_username:
            continue
        
        reply_type = parse_reply_type(comment.get("body", ""))
        if reply_type:
            return {
                "session_id": session_id,
                "issue_number": issue_number,
                "reporter": reporter_username,
                "reply_type": reply_type,
                "comment_time": comment.get("createdAt"),
                "comment_body": comment.get("body", "")[:200]  # Truncate for display
            }
    
    return None


def list_active_sessions() -> List[str]:
    """List all active (in_progress) bisect sessions."""
    if not SESSIONS_DIR.exists():
        return []
    
    sessions = []
    for json_file in SESSIONS_DIR.glob("*.json"):
        session_id = json_file.stem
        session = load_session(session_id)
        if session and session.get("status") == "in_progress":
            sessions.append(session_id)
    
    return sessions


def main():
    """Main entry point."""
    verbose = "--verbose" in sys.argv
    
    # Get active sessions
    active_sessions = list_active_sessions()
    
    if not active_sessions:
        # No active sessions - silent
        return
    
    # Check each session for new replies
    found_replies = []
    
    for session_id in active_sessions:
        result = check_session(session_id, verbose)
        if result and "error" not in result:
            found_replies.append(result)
    
    if found_replies:
        # New replies found - report them
        for reply in found_replies:
            print(f"\nSession {reply['session_id']} (Issue #{reply['issue_number']})")
            print(f"  Reporter: {reply['reporter']}")
            print(f"  Reply type: {reply['reply_type'].upper()}")
            print(f"  Time: {reply['comment_time']}")
            print(f"  Comment preview: \"{reply['comment_body']}\"...")
    else:
        # No new replies - silent output for cron job
        print("[SILENT]")


if __name__ == "__main__":
    main()
