# Testing Patterns Reference

Additional patterns and examples for adapting the telegram-bisect-test to different workflows.

## Pattern 1: Simple Binary Search Testing

For testing a range of items where you just need to find the boundary between pass/fail:

```python
# In config.py, adjust keyword sets for your use case:
GOOD_KEYWORDS = {"pass", "ok", "works"}
BAD_KEYWORDS = {"fail", "broken", "not ok"}

# The binary search logic in manage-sessions.py will automatically narrow down
# the boundary between good and bad items.
```

## Pattern 2: Multi-Stage Testing

For workflows with more than just pass/fail (e.g., triage stages):

```python
# In telegram_handler.py, modify parse_reply_type():
def parse_reply_type(body: str) -> Optional[str]:
    text = body.lower().strip()
    
    if "urgent" in text or "critical" in text:
        return "urgent"
    if "good" in text or "pass" in text:
        return "good"
    if "bad" in text or "fail" in text:
        return "bad"
    if "needs info" in text or "clarify" in text:
        return "needs_info"
    
    return None

# Then handle each response type differently in the handler.
```

## Pattern 3: Custom Action on Response

Instead of just tracking state, take immediate action when a response is found:

```python
# In telegram_handler.py, after updating the session:

if reply_type == "good":
    # Trigger a follow-up task or notification
    subprocess.run(["./trigger-next-task.sh", active_session])

elif reply_type == "bad":
    # Open a ticket or send alert
    subprocess.run(["./create-ticket.sh", active_session])

# Or use the Telegram API to send a different message based on response type.
```

## Pattern 4: Email/Notification Integration

Send notifications when responses are found:

```python
# Add to telegram_handler.py imports:
import smtplib
from email.mime.text import MIMEText

def send_email_notification(session_id: str, reply_type: str):
    """Send email notification about a response."""
    msg = MIMEText(f"""
Response received for session {session_id}:

Type: {reply_type.upper()}
Time: {datetime.utcnow().isoformat()}

Please review and take appropriate action.
""")
    msg['Subject'] = f"Test Response: Session {session_id}"
    msg['From'] = "notifications@example.com"
    msg['To'] = "admin@example.com"
    
    with smtplib.SMTP("smtp.example.com") as server:
        server.send_message(msg)

# Call send_email_notification() after processing each response.
```

## Pattern 5: Slack/Discord Integration

Post to a chat channel when responses are found:

```python
# Add webhook URL to config.py:
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

# In telegram_handler.py, add:
import requests

def post_to_slack(session_id: str, reply_type: str):
    """Post a notification to Slack."""
    payload = {
        "text": f"Response for session {session_id}: {reply_type.upper()}"
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

# Call post_to_slack() after processing each response.
```

## Pattern 6: Webhook Integration for External Systems

Integrate with external systems via webhooks when responses are found:

```python
# In telegram_handler.py, add:
import requests

def notify_external_system(session_id: str, reply_type: str):
    """Notify external system about response."""
    payload = {
        "session_id": session_id,
        "reply_type": reply_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    requests.post("https://your-system.com/webhook/test-response", json=payload)

# Call notify_external_system() after processing each response.
```

## Session JSON Schema Reference

```json
{
  "session_id": "string - unique identifier",
  "reporter": "string - username of the person being tracked",
  "status": "string - 'in_progress' or 'converged'",
  "range": {
    "start": "integer - start of test range",
    "end": "integer - end of test range"
  },
  "last_step": {
    "step_number": "integer - current step number",
    "item": "integer - item being tested (or None if converged)",
    "timestamp": "ISO 8601 timestamp of last step",
    "result": "string - 'good' or 'bad'"
  },
  "notes": "string - any additional notes about the session"
}
```

## Troubleshooting

### "No active session found for @username"
Start a new session: `python3 manage-sessions.py start "1..50" your-username`

### "Telegram API error: 401 Unauthorized"
Check that TELEGRAM_BOT_TOKEN in config.py is correct and not expired.

### "Session not found"
Check that the session file exists in SESSIONS_DIR and has valid JSON.

### "Import error: scripts.manage_sessions"
Ensure you're running the script from within the skill directory, or adjust the import path.

### "HTTP 404 for webhook"
Make sure your Telegram bot's webhook URL is set correctly:
```bash
curl -X POST "https://api.telegram.org/bot<token>/setWebhook" \
  -d "url=https://your-domain.com:8080/telegram/webhook"
```

## Example Use Cases

### 1. Testing a Range of Numbers
Test which numbers in a range are prime:
```bash
python3 manage-sessions.py start "1..100" tester
# System will ask you to confirm if each number is prime (GOOD=prime, BAD=not prime)
```

### 2. Bug Bisect Practice
Practice bisecting a known bug range:
```bash
python3 manage-sessions.py start "100..200" tester
# System will narrow down the first bad commit based on your responses
```

### 3. Feature Acceptance Testing
Test feature acceptance across a range of scenarios:
```bash
python3 manage-sessions.py start "1..50" qa-team
# QA team responds GOOD/BAD for each scenario
```

### 4. Support Ticket Triage
Practice triaging support tickets:
```bash
python3 manage-sessions.py start "1..25" triage-team
# Team responds with priority level (adapt keywords for this use case)
```
