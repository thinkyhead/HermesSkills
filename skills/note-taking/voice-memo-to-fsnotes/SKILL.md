---
name: voice-memo-to-fsnotes
description: Reference skill for the Voice Memo → FSNotes pipeline. Documents the note format, Buzz CLI usage, and Buzz model types. The actual transcription, note writing, and conditional Hermes invocation are handled entirely by the `transcribe_new_memos.sh` script from the `setup-voice-memo-pipeline` skill.
tags: [voice-memo, fsnotes, buzz, whisper, transcription, macos, audio]
related_skills: [fsnotes, background-tts]
platforms: [macos]
---

# Voice Memo to FSNotes

Converts Apple Voice Memo recordings into structured FSNotes with transcribed text.
Uses Buzz (https://github.com/chidiwilliams/buzz) for offline transcription via whisper.cpp —
no Python env or conda required.

## Transcription Options

### Buzz (Recommended for offline use)

Buzz provides a simple CLI interface with whisper.cpp models. See the Buzz documentation
for installation and usage details.

### Other Options

Several other transcription approaches are available depending on your needs:

- **Nous Research models** - Local inference with quantized models via MLX (Apple Silicon) or llama.cpp
- **OpenRouter** - Cloud-based transcription using various models, useful when local resources are limited
- **Local whisper.cpp** - Direct usage without the Buzz wrapper for more control over parameters

The choice depends on your priorities: offline privacy (Buzz/local), convenience/speed (cloud), or fine-grained control (direct whisper.cpp).

## Source Location

Voice Memo recordings live here:

  RECORDINGS="$HOME/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"

Buzz is invoked with `-d` so `.txt` output goes directly to hermes/ — no audio copy needed:

  HERMES_DIR="$RECORDINGS/hermes"

Files are named like: `20260422 174918.m4a`
(date + time; may or may not have a hex suffix)

## Destination

  FSNOTES="$HOME/Library/Mobile Documents/iCloud~co~fluder~fsnotes/Documents"

Voice memo notes go in a dedicated subfolder:

  VOICE_NOTES="$FSNOTES/Voice Memos"

Create it if needed:
```bash
mkdir -p "$VOICE_NOTES"
```

## Dependencies

### Buzz (macOS app with bundled CLI)

Latest release: https://github.com/chidiwilliams/buzz/releases/latest

**macOS ARM64:** `Buzz-x.x.x-mac-ARM64.dmg` (from SourceForge link on releases page)

**Install:** download DMG -> drag Buzz.app to /Applications

After install, the CLI is available at:
```bash
/Applications/Buzz.app/Contents/MacOS/Buzz
```

Add to PATH for convenience (add to `~/.zshrc`):
```bash
alias buzz="/Applications/Buzz.app/Contents/MacOS/Buzz"
```

## Division of Labor

The `transcribe_new_memos.sh` script (from the `setup-voice-memo-pipeline` skill) is the full automation engine:
  - Debouncing, sentinel tracking, Buzz transcription
  - Building and writing FSNotes directly to disk
  - Detecting "hey hermes" in the transcript and invoking Hermes only when addressed

Hermes is invoked **only** when a voice memo transcript contains "hey hermes".
The script sends only the instruction text to Hermes — no audio files or paths are passed.

## Responding to "hey hermes" memos

When Hermes receives a prompt like `"Voice memo instruction: <text>"`, it carries out the
requested task using whatever toolsets were granted. The transcript and note path are NOT
provided — only the instruction text was sent by the script.

If the instruction was successfully completed, a brief TTS confirmation is a nice touch:
  - Use `background-tts` skill, or
  - Run: `launchctl asuser 501 /usr/bin/say "Done."`

## Note format (for reference — written by the shell script)

```markdown
# Voice Memo YYYY-MM-DD HH:MM

> Voice Memo recorded YYYY-MM-DD at HH:MM
> Source: `/path/to/original.m4a`

---

<transcript>

---
```

## Pitfalls

- The Recordings path contains spaces — always quote it in shell commands.
- `.txt` output lands in the same folder as the input `.m4a`, not a configurable output dir.
- Buzz must be installed at `/Applications/Buzz.app` for the CLI path to work.
- First run downloads the model — allow extra time (~1–2 min on first use).
- `--hide-gui` suppresses the Buzz window; omit it if you want to watch progress visually.
- iCloud may not have synced all recordings locally; check RECORDINGS folder for missing memos.
- Filenames include a hex suffix (e.g. `-24A17D80`) — strip it when building note titles.
- Always embed the original `.m4a` path in the note for future reference/playback.
