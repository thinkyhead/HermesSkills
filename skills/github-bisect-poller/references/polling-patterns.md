# Polling Patterns Reference

Additional patterns and examples for adapting the github-bisect-poller to different workflows.

## Pattern 1: Simple Status Polling

For issues where you just need to know if there's any new activity (not specific GOOD/BAD responses):

```python
# In poll-bisect-replies.py, modify parse_reply_type():
def parse_reply_type(body: str) -> Optional[str]:
    """Parse a comment body to determine if there's any new activity."""
    text = body.lower().strip()
    
    # Check for any substantive response (not just "thanks" or "checking")
    if len(text) > 20 and text not in ("thanks", "ok", "got it", "checking"):
        return "activity"
    
    return None
```

## Pattern 2: Multiple Response Types

For workflows with more than just GOOD/BAD responses:

```python
# In config.py, add more keyword sets:
NEEDS_INFO_KEYWORDS = {"need info", "more details", "clarify", "unclear"}
DUPLICATE_KEYWORDS = {"duplicate", "same as", "already reported"}

# In poll-bisect-replies.py, modify parse_reply_type():
def parse_reply_type(body: str) -> Optional[str]:
    text = body.lower().strip()
    
    for keyword in NEEDS_INFO_KEYWORDS:
        if keyword in text:
            return "needs_info"
    
    for keyword in DUPLICATE_KEYWORDS:
        if keyword in text:
            return "duplicate"
    
    # ... existing GOOD/BAD logic ...
```

## Pattern 3: Timestamp-Based Cutoff

Instead of checking all comments, only check for replies after a specific timestamp:

```python
# In poll-bisect-replies.py, modify check_session():
def check_session(session_id: str, verbose: bool = False) -> Optional[Dict]:
    session = load_session(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    
    # Get the timestamp of the last step (if any)
    last_step = session.get("last_step")
    if last_step and "timestamp" in last_step:
        cutoff_time = datetime.fromisoformat(last_step["timestamp"].replace("Z", "+00:00"))
    else:
        cutoff_time = None
    
    # Fetch all comments and filter by timestamp
    comments = get_issue_comments(session.get("issue_number"))
    
    for comment in comments:
        if comment.get("login") != session.get("reporter"):
            continue
        
        # Skip comments before the cutoff
        if cutoff_time:
            comment_time = datetime.fromisoformat(comment.get("createdAt").replace("Z", "+00:00"))
            if comment_time <= cutoff_time:
                continue
        
        reply_type = parse_reply_type(comment.get("body", ""))
        if reply_type:
            return {...}  # Return the response
    
    return None
```

## Pattern 4: Custom Action on Response

Instead of just reporting, take immediate action when a response is found:

```python
# In poll-bisect-replies.py, modify main():
def main():
    active_sessions = list_active_sessions()
    
    if not active_sessions:
        return
    
    found_replies = []
    
    for session_id in active_sessions:
        result = check_session(session_id, verbose)
        if result and "error" not in result:
            found_replies.append(result)
            
            # Custom action on response
            if result["reply_type"] == "good":
                # Trigger a build or notification
                subprocess.run(["./trigger-build.sh", session_id])
    
    if found_replies:
        for reply in found_replies:
            print(f"\nSession {reply['session_id']} (Issue #{reply['issue_number']})")
            print(f"  Reporter: {reply['reporter']}")
            print(f"  Reply type: {reply['reply_type'].upper()}")
    else:
        print("[SILENT]")
```

## Pattern 5: Email/Notification Integration

Send notifications when responses are found:

```python
# Add to poll-bisect-replies.py imports:
import smtplib
from email.mime.text import MIMEText

def send_notification(session_id: str, reply: Dict):
    """Send email notification about a new response."""
    msg = MIMEText(f"""
New response found for session {session_id}:

Issue: #{reply['issue_number']}
Reporter: {reply['reporter']}
Reply type: {reply['reply_type'].upper()}
Time: {reply['comment_time']}

Preview: "{reply['comment_body'][:100]}..."
""")
    msg['Subject'] = f"GitHub Response: Issue #{reply['issue_number']}"
    msg['From'] = "notifications@example.com"
    msg['To'] = "admin@example.com"
    
    with smtplib.SMTP("smtp.example.com") as server:
        server.send_message(msg)

# In main(), call send_notification() when a reply is found.
```

## Pattern 6: Slack/Discord Integration

Post to a chat channel when responses are found:

```python
# Add webhook URL to config.py:
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

# In poll-bisect-replies.py, add:
import requests

def post_to_slack(reply: Dict):
    """Post a notification to Slack."""
    payload = {
        "text": f"New response for session {reply['session_id']} (Issue #{reply['issue_number']})\n"
                f"Reporter: {reply['reporter']}\n"
                f"Type: {reply['reply_type'].upper()}"
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

# In main(), call post_to_slack() when a reply is found.
```

## Session JSON Schema Reference

```json
{
  "session_id": "string - unique identifier",
  "issue_number": "integer - GitHub issue number",
  "reporter": "string - username of the person being tracked",
  "status": "string - 'in_progress' or 'converged'",
  "last_step": {
    "step_number": "integer - current step number",
    "sha": "string - commit SHA being tested (if applicable)",
    "build_url": "string - URL to build/artifact",
    "timestamp": "ISO 8601 timestamp of last step"
  },
  "notes": "string - any additional notes about the session"
}
```

## Troubleshooting

### "No sessions directory found"
Create the directory manually: `mkdir -p ~/.hermes/github-bisect-sessions`

### "gh command failed"
Ensure you're authenticated: `gh auth status`

### "Session not found"
Check that the session file exists in SESSIONS_DIR and has valid JSON.

### "Failed to fetch issue comments"
Check that the repo name is correct in config.py and you have access to the issues.
