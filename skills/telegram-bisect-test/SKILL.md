---
name: telegram-bisect-test
description: Generic Telegram-driven bisect test workflow. Allows practicing issue response tracking via Telegram DMs instead of GitHub comments. Useful for testing bisect workflows, triage automation, or any scenario where you need to poll for responses and take action based on them.
tags: [telegram, bisect, testing, automation, issues]
related_skills: [github-bisect-poller]
platforms: [linux, macos, windows]
---

# Telegram Bisect Test Workflow

Generic workflow for practicing issue response tracking via Telegram DMs. Instead of polling GitHub comments, you (or a tester) respond directly on Telegram, and the system takes action based on your responses.

## Use Cases

- **Testing bisect workflows** - Practice the full cycle without waiting for external reporters
- **Triage automation testing** - Test automated response systems in a controlled environment
- **Support workflow simulation** - Practice handling customer responses to troubleshooting steps
- **Any polling-based response system** - Adapt the keyword patterns and actions as needed

## How It Works

1. **Start a session** - Define the range of items/issues to test
2. **System proposes actions** - Sends you a task or question via Telegram
3. **You respond** - Reply with your decision (GOOD/BAD, accept/reject, etc.)
4. **System takes action** - Based on your response, it performs the next step or advances
5. **Repeat until complete** - Continue until the test range is exhausted

## Quick Start

### Configuration

Edit `config.py` to set your Telegram bot and session paths:

```python
TELEGRAM_BOT_TOKEN = "your-bot-token"  # From @BotFather
TELEGRAM_CHAT_ID = "your-chat-id"      # Your Telegram user ID or group ID
SESSIONS_DIR = Path.home() / ".hermes/telegram-bisect-sessions"
```

### Starting a Session

Create a new session:

```bash
python3 scripts/manage-sessions.py start \
  --range "1..50" \
  --reporter your-username
```

This creates a session that will test items 1 through 50.

### Receiving Tasks via Telegram

The system sends you tasks/messages on Telegram:

```
🔬 **Test session started** — session `<session-id>`

Range: 50 items to test
Max steps: ~6 (logarithmic)

I'll send you a task for each step. Reply **GOOD** or **BAD** to proceed.

Processing item 25 now...
```

### Responding on Telegram

Reply with your decision:

- **GOOD** - Item passes / issue not present
- **BAD** - Item fails / issue present

The system will then:
1. Record your response
2. Calculate the next step (if not converged)
3. Send you the next task via Telegram

### Viewing Session Status

```bash
python3 scripts/manage-sessions.py status <session-id>
```

## Session Structure

Each session is tracked in a JSON file:

```json
{
  "session_id": "abc123",
  "reporter": "username",
  "status": "in_progress",
  "range": {"start": 1, "end": 50},
  "last_step": {
    "step_number": 3,
    "item": 25,
    "timestamp": "2026-06-01T12:00:00Z"
  },
  "notes": ""
}
```

## Keyword Patterns

Edit `config.py` to customize what counts as each response type:

```python
GOOD_KEYWORDS = {"good", "pass", "works", "ok", "accepted"}
BAD_KEYWORDS = {"bad", "fail", "broken", "rejected", "not ok"}
```

You can also add custom parsing logic in `parse_reply_type()` if your workflow needs more sophisticated detection.

## Adapting to Your Workflow

### Change the range being tested

```python
# In manage-sessions.py start command:
--range "100..200"  # Test items 100-200
```

### Change what counts as a response

Edit the keyword sets in `config.py` or add custom parsing logic.

### Change where sessions are stored

```python
SESSIONS_DIR = Path("/custom/path/to/sessions")
```

### Add custom actions on response

Modify `manage-sessions.py` to call additional scripts or APIs when a specific response type is found.

## Scripts

- `manage-sessions.py` - Session management (start, status, advance, close)
- `telegram_handler.py` - Telegram bot handler for receiving responses

## Pitfalls

- Always match responses against the **reporter's** username stored in the session JSON
- The last step's timestamp is the cutoff — don't re-process old replies
- Don't advance on ambiguous replies; accuracy matters more than speed
- After advancing, re-read the session JSON before any further commands

## Reference

See `references/testing-patterns.md` for additional patterns and examples.
