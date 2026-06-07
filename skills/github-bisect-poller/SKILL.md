---
name: github-bisect-poller
description: Generic GitHub issue polling workflow for tracking reporter responses and advancing bisect sessions. Adaptable to any repo where you need to poll issues for specific response patterns and take action based on them.
tags: [github, polling, bisect, automation, issues]
related_skills: []
platforms: [linux, macos, windows]
---

# GitHub Bisect Poller

Generic workflow for polling GitHub issues for specific response patterns and taking action based on them. Originally designed for Marlin firmware bisect sessions, this can be adapted to any repo where you need to:

1. Track active issue sessions
2. Poll for new comments from specific users (reporters)
3. Parse responses for keywords or patterns
4. Take action based on the response type

## Use Cases

- **Bug bisect workflows** - Track reporter responses to test builds
- **Issue triage automation** - Poll for updates on pending issues
- **Support ticket workflows** - Track customer responses to troubleshooting steps
- **Any polling-based response system** - Adapt the keyword patterns and actions as needed

## Quick Start

### Configuration

Edit `config.py` to set your repo and session paths:

```python
GITHUB_REPO = "YourOrg/YourRepo"  # e.g., "MarlinFirmware/Marlin"
SESSIONS_DIR = Path.home() / ".hermes/your-bisect-sessions"  # Where session JSONs live
```

### Poll for New Responses

Run the poller script:

```bash
python3 scripts/poll-bisect-replies.py [--verbose]
```

**Output format:**
- If new responses found: Reports session details with response type
- If no updates: `[SILENT]` (for cron jobs that should be quiet)

### View Active Sessions

```bash
python3 scripts/manage-sessions.py list
```

### Advance a Session

When you find a clear response:

```bash
python3 scripts/manage-sessions.py advance --session <id> --result good|bad|other
```

## Session Structure

Each active session is tracked in a JSON file:

```json
{
  "session_id": "abc123",
  "issue_number": 42,
  "reporter": "username",
  "status": "in_progress",
  "last_step": {
    "step_number": 3,
    "sha": "abc123def",
    "build_url": "...",
    "timestamp": "2026-06-01T12:00:00Z"
  },
  "notes": ""
}
```

## Keyword Patterns

Edit `config.py` to customize what counts as each response type:

```python
GOOD_KEYWORDS = {"good", "works", "fixed", "resolved"}
BAD_KEYWORDS = {"bad", "broken", "still fails", "error"}
```

You can also add custom parsing logic in `parse_reply_type()` if your workflow needs more sophisticated detection.

## Cron Job Integration

For scheduled polling, use the poller in a cron job:

```bash
# Run every 30 minutes, only notify when there's work to do
*/30 * * * * python3 /path/to/poll-bisect-replies.py | grep -v "^\[SILENT\]$"
```

The script outputs `[SILENT]` when there's nothing to report, so you can filter it out or use it as a silent health check.

## Adapting to Your Workflow

### Change the repo being tracked

```python
GITHUB_REPO = "YourOrg/YourRepo"
```

### Change what counts as a response

Edit the keyword sets in `config.py` or add custom parsing logic.

### Change where sessions are stored

```python
SESSIONS_DIR = Path("/custom/path/to/sessions")
```

### Add custom actions on response

Modify `poll-bisect-replies.py` to call additional scripts or APIs when a specific response type is found.

## Scripts

- `poll-bisect-replies.py` - Main poller script for cron jobs
- `manage-sessions.py` - Session management (list, advance, create)

## Pitfalls

- Always match comments against the **reporter's** username stored in the session JSON
- The last step's timestamp is the cutoff — don't re-process old replies
- Don't advance on ambiguous replies; accuracy matters more than speed
- After advancing, re-read the session JSON before any further commands

## Reference

See `references/polling-patterns.md` for additional patterns and examples.
