# Hermes Skills

A collection of reusable, well-documented workflows and procedures for the Hermes Agent platform. These skills are designed to be copied into your local `~/.hermes/skills/` directory and used immediately.

## Available Skills

### note-taking/fsnotes

**Read, search, create, and edit notes in FSNotes on macOS.** Notes are plain Markdown files or .textbundle directories stored in iCloud and synced across devices.

**Use this skill when you need to:**
- Manage notes stored in FSNotes without using the app directly
- Search note contents via CLI tools
- Create or edit notes programmatically
- Handle both plain `.md` files and TextBundle format

**See:** `skills/note-taking/fsnotes/SKILL.md` for full documentation.

---

### note-taking/voice-memo-to-fsnotes

**Convert Apple Voice Memo recordings into structured FSNotes with transcribed text.** Uses Buzz (whisper.cpp-based) for offline transcription, or can be adapted to use Nous Research models, OpenRouter, or direct whisper.cpp usage.

**Use this skill when you need to:**
- Transcribe voice memos and store them as FSNotes
- Set up automated transcription pipelines
- Choose between different transcription backends (offline vs cloud)

**See:** `skills/note-taking/voice-memo-to-fsnotes/SKILL.md` for full documentation.

---

### note-taking/voice-memo-setup

**Set up automatic transcription of Apple Voice Memos to FSNotes using macOS Folder Actions.** Installs Buzz for offline transcription, creates the transcription script, sets up an Automator workflow, and attaches it to the Voice Memos Recordings folder.

**Use this skill when you need to:**
- Automatically transcribe Voice Memos as they're recorded
- Set up a complete Folder Action workflow from scratch
- Customize the transcription process for different note formats

**See:** `skills/voice-memo-setup/SKILL.md` for full documentation.

---

### github-bisect-poller

**Generic GitHub issue polling workflow for tracking reporter responses and advancing bisect sessions.** Adaptable to any repo where you need to poll issues for specific response patterns and take action based on them.

**Use this skill when you need to:**
- Track bug bisect sessions and advance based on reporter responses
- Poll GitHub issues for specific keywords or patterns
- Set up cron jobs that silently check for updates
- Adapt the workflow to your own issue tracking needs

**See:** `skills/github-bisect-poller/SKILL.md` for full documentation.

---

### telegram-bisect-test

**Telegram-driven bisect test workflow for practicing issue response tracking via Telegram DMs.** Instead of polling GitHub comments, you respond directly on Telegram and the system takes action based on your responses.

**Use this skill when you need to:**
- Practice bisect workflows without waiting for external reporters
- Test automated response systems in a controlled environment
- Set up a Telegram bot that receives responses and updates session state
- Adapt the workflow to any polling-based response system

**See:** `skills/telegram-bisect-test/SKILL.md` for full documentation.

---

## How to Use These Skills

1. **Copy a skill** into your local skills directory:
   ```bash
   cp -r ~/.hermes/skills/note-taking/fsnotes ~/.hermes/profiles/<your-profile>/skills/
   ```

2. **Configure** the skill by editing `config.py` if present, setting paths and options for your environment.

3. **Use the skill** by invoking it in a Hermes session:
   ```bash
   hermes -p <profile> --skills <skill-name> chat
   ```

4. **Run scripts** directly if the skill includes automation:
   ```bash
   python3 ~/.hermes/skills/github-bisect-poller/scripts/poll-bisect-replies.py
   ```

## Repository Structure

```
HermesSkills/
├── LICENSE              # MIT License
├── README.md            # This file
└── skills/              # Individual skill definitions
    └── <skill-name>/
        ├── SKILL.md     # Main documentation (YAML frontmatter + markdown)
        └── references/  # Optional supporting docs
        ├── templates/   # Optional templates
        └── scripts/     # Optional helper scripts
```

## License

All content in this repository is released under the MIT License. See `LICENSE` for full text.

---

*This repository is maintained by Scott Lahteine (Thinkyhead) and published to the thinkyhead GitHub account.*
