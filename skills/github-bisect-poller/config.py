#!/usr/bin/env python3
"""
Configuration for github-bisect-poller

Edit these values to adapt the poller to your repo and workflow.
"""

from pathlib import Path

# GitHub repo being tracked (e.g., "MarlinFirmware/Marlin")
GITHUB_REPO = "YourOrg/YourRepo"

# Directory where session JSON files are stored
SESSIONS_DIR = Path.home() / ".hermes/github-bisect-sessions"

# Keywords that indicate a positive response (bug is fixed)
GOOD_KEYWORDS = {
    "good", "works", "fixed", "resolved", "clean", 
    "it works", "not present", "no bug", "bug not present"
}

# Keywords that indicate a negative response (bug still present)
BAD_KEYWORDS = {
    "bad", "broken", "still fails", "error", "same issue", 
    "still broken", "fails", "crashing", "bug present"
}

# How many recent comments to check per issue (default: 10)
MAX_COMMENTS_TO_CHECK = 10
