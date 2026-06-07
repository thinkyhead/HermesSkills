---
name: voice-memo-setup
description: Set up automatic transcription of Apple Voice Memos to FSNotes using macOS Folder Actions. Installs Buzz for offline transcription, creates the transcription script, sets up an Automator workflow, and attaches it to the Voice Memos Recordings folder.
tags: [voice-memo, fsnotes, automator, folder-action, macos, transcription]
related_skills: [voice-memo-to-fsnotes, fsnotes]
platforms: [macos]
---

# Voice Memo Setup: Automatic Transcription to FSNotes

Automatically transcribes Apple Voice Memos and saves them as structured Markdown notes in FSNotes. Triggered by a macOS Folder Action whenever a new `.m4a` recording lands in the Voice Memos Recordings folder.

## Overview

```
Voice Memos app
  -> saves .m4a to Recordings/
  -> Folder Action fires
  -> transcribe_new_memos.sh (debounced, copies file to hermes/)
  -> Buzz CLI transcribes via whisper.cpp
  -> FSNote created in FSNotes/Voice Memos/
  -> if transcript says "hey hermes": Hermes invoked with the instruction
  -> work files cleaned up
```

## Use Cases

- **Personal voice memo management** - Automatically save transcribed memos to your note-taking system
- **Meeting notes automation** - Record meetings and get instant transcripts saved as notes
- **Idea capture** - Capture ideas via voice and have them immediately available in your notes
- **Customizable workflow** - Adapt the transcription script for different note formats or destinations

## Prerequisites

- macOS with Voice Memos and FSNotes installed
- Hermes Agent installed at `~/.local/bin/hermes` (optional - can be removed if not needed)
- Terminal automation permission for System Events:
  - System Settings -> Privacy & Security -> Automation -> enable Terminal (or your shell)

## Quick Start

### Step 1: Install Buzz

Buzz is a native macOS app that bundles whisper.cpp for offline transcription. No Python or conda environment required.

Download the latest release from:
```
https://github.com/chidiwilliams/buzz/releases/latest
```

**macOS ARM64:** `Buzz-x.x.x-mac-ARM64.dmg`  
**macOS Intel:** `Buzz-x.x.x-mac-X64.dmg`

(Available via the SourceForge link on the releases page)

Install steps:
1. Mount the DMG and drag `Buzz.app` to `/Applications`
2. Clear the quarantine attribute:
   ```bash
   xattr -dr com.apple.quarantine /Applications/Buzz.app
   ```
3. Verify:
   ```bash
   /Applications/Buzz.app/Contents/MacOS/Buzz --version
   ```

Optionally add a shell alias (e.g., in `~/.zshrc`):
```bash
alias buzz="/Applications/Buzz.app/Contents/MacOS/Buzz"
```

On first transcription run, Buzz will download the whisper.cpp model (~460 MB for small).

### Step 2: Create the hermes/ working directory

```bash
RECORDINGS="$HOME/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
HERMES_DIR="$RECORDINGS/hermes"
mkdir -p "$HERMES_DIR"
touch "$HERMES_DIR/.last_transcribed"
touch "$HERMES_DIR/.last_run"
```

The Folder Action watches the parent `Recordings/` folder. All work files (copies, transcripts, logs) are kept in `hermes/` so they don't re-trigger the Folder Action.

### Step 3: Install the transcription script

Copy the script template from this skill into the `hermes/` directory:

```bash
cp /Users/thinkyhead/.hermes/skills/voice-memo-setup/scripts/transcribe_new_memos.sh \
  "$HERMES_DIR/transcribe_new_memos.sh"
chmod +x "$HERMES_DIR/transcribe_new_memos.sh"
```

The script uses `$HOME` throughout and requires no edits for a standard installation.

### Step 4: Install the Automator Folder Action workflow

Create the workflow bundle directory and copy the template:

```bash
WORKFLOW_DIR="$HOME/Library/Workflows/Applications/Folder\ Actions/Transcribe\ Voice\ Memos.workflow"
mkdir -p "$WORKFLOW_DIR/Contents"
cp /Users/thinkyhead/.hermes/skills/voice-memo-setup/templates/document.wflow \
  "$WORKFLOW_DIR/Contents/document.wflow"
```

The workflow contains three actions:
- **Get Specified Text:** passes "Memo Received." downstream
- **Speak Text:** speaks the notification aloud (Eddy voice, English UK)
- **Run Shell Script:** calls `transcribe_new_memos.sh` via exec

To change the notification voice, open the workflow in Automator after installation and adjust the "Speak Text" action.

### Step 5: Attach the Folder Action via AppleScript

Copy and run the attach script:

```bash
cp /Users/thinkyhead/.hermes/skills/voice-memo-setup/scripts/attach_folder_action.applescript \
  /tmp/attach_folder_action.applescript
osascript /tmp/attach_folder_action.applescript
```

**PITFALL:** The workflow path must be converted from POSIX to HFS (colon-separated) format before passing to System Events. Passing a POSIX string directly to `make new script` fails with error -43. The provided script handles this correctly.

Verify the attachment succeeded:
```bash
osascript /Users/thinkyhead/.hermes/skills/voice-memo-setup/scripts/verify_folder_action.applescript
```

Expected output:
```
Folder Action on: /Users/<you>/Library/Group Containers/...
Scripts: UltraHD:Users:<you>:Library:Workflows:...
Enabled: true
```

### Step 6: Verify end to end

1. Make a test recording in Voice Memos (say something clearly).
2. Wait a few seconds — you should hear "Memo Received." spoken aloud.
3. Check the log:
   ```bash
   tail "$HERMES_DIR/.transcribe_action.log"
   ```
4. Check FSNotes for a new note in the "Voice Memos" folder.

## Note Format

The transcription script creates notes with this format:

```markdown
# Voice Memo YYYY-MM-DD HH:MM

> Voice Memo recorded YYYY-MM-DD at HH:MM
> Source: `/absolute/path/to/voice.m4a`

---

<transcript>

---
```

## Customization Options

### Remove Hermes Invocation

If you don't need the "hey hermes" feature, edit `transcribe_new_memos.sh` and remove lines 128-139 (the `if [[ "$TRANSCRIPT_LOWER" =~ hey\ hermes ]]` block).

### Change Notification Voice

Open the workflow in Automator:
1. Open `~/Library/Workflows/Applications/Folder\ Actions/Transcribe\ Voice\ Memos.workflow`
2. Select the "Speak Text" action
3. Change the voice in the dropdown (try different voices to find your preference)

### Adjust Transcription Quality

Edit `transcribe_new_memos.sh` line 86 to use a different whisper.cpp model:
- `tiny` - Fastest, lower accuracy (~75 MB)
- `base` - Faster, decent accuracy (~140 MB)
- `small` - Slower, better accuracy (~260 MB)
- `medium` - Slowest, best accuracy (~780 MB)

Example: Change `whispercpp tiny` to `whispercpp small` for better accuracy.

### Change Note Destination

Edit `transcribe_new_memos.sh` line 43 to change where notes are saved:
```bash
VOICE_NOTES="$FSNOTES/YourCustomFolder"
```

## Uninstall

To remove the pipeline (originals in `Recordings/` are never touched):

1. Detach the Folder Action via System Events (or Folder Actions Setup app)
2. Remove the workflow bundle from `~/Library/Workflows/Applications/Folder Actions/`
3. Remove the `hermes/` working directory from inside `Recordings/`:
   ```bash
   rm -rf "$HOME/Library/Group\ Containers/group.com.apple.VoiceMemos.shared/hermes"
   ```
4. Optionally remove Buzz from `/Applications/`

## Pitfalls

- Folder Actions must be enabled system-wide in System Events.
- Terminal (or your shell) needs Automation permission for System Events:
  - System Settings -> Privacy & Security -> Automation
- The Recordings folder path contains spaces — always quote it in shell commands.
- Buzz downloads its whisper.cpp model on first use (~460 MB for small model).
- If the Folder Action fires but nothing happens, check `.transcribe_action.log`.
- The "Speak Text" step uses Eddy (English UK); change it in Automator if preferred.
- Hermes must be reachable at `~/.local/bin/hermes` or adjust the path in the script.

## Reference Files

- `scripts/transcribe_new_memos.sh` - Main transcription and note-writing script
- `templates/document.wflow` - Automator workflow template
- `scripts/attach_folder_action.applescript` - Script to attach the Folder Action
- `scripts/verify_folder_action.applescript` - Script to verify attachment

---

*This skill is maintained by Scott Lahteine (Thinkyhead) and published to the thinkyhead GitHub account.*
