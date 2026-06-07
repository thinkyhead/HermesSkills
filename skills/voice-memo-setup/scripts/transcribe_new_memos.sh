#!/bin/zsh
# Folder Action script: transcribe new Voice Memos to FSNotes.
# If the transcript addresses "hey hermes", also invoke Hermes.
# Otherwise, save the note to FSNotes without involving Hermes.
#
# Authors: Thinkyhead, Hermes
# Part of the setup-voice-memo-pipeline / voice-memo-to-fsnotes skill pair.
#
# Division of labor:
#   This script (hermes/ subdirectory):
#     - Debounces Folder Action firings (5 s window)
#     - Tracks sentinels so only new memos are processed
#     - Copies .m4a into hermes/ (prevents re-triggering)
#     - Runs Buzz CLI for transcription (whispercpp model)
#     - Writes an FSNote Markdown file directly (note format below)
#     - Detects "hey hermes" in the transcript and invokes Hermes
#       only when the memo is addressed to Hermes
#
#   Hermes (via the voice-memo-to-fsnotes skill when invoked):
#     - Acts on the embedded instruction after "hey hermes"
#     - Receives only the instruction text (not the audio or file paths)
#
# Note format (written by this script):
#   # Voice Memo YYYY-MM-DD HH:MM
#
#   > Voice Memo recorded YYYY-MM-DD at HH:MM
#   > Source: `/absolute/path/to/voice.m4a`
#
#   ---
#
#   <transcript>
#
#   ---

RECORDINGS="$HOME/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
HERMES_DIR="$RECORDINGS/hermes"
SENTINEL="$HERMES_DIR/.last_transcribed"
LAST_RUN="$HERMES_DIR/.last_run"
LOGFILE="$HERMES_DIR/.transcribe_action.log"
HERMES="$HOME/.local/bin/hermes"
BUZZ="/Applications/Buzz.app/Contents/MacOS/Buzz"
FSNOTES="$HOME/Library/Mobile Documents/iCloud~co~fluder~fsnotes/Documents"
VOICE_NOTES="$FSNOTES/Voice Memos"

# ── Debounce ──────────────────────────────────────────────────
NOW=$(date +%s)
if [ -f "$LAST_RUN" ]; then
  LAST_TS=$(stat -f %m "$LAST_RUN" 2>/dev/null || echo 0)
  ELAPSED=$(( NOW - LAST_TS ))
  touch "$LAST_RUN"
  [ "$ELAPSED" -lt 5 ] && exit 0
fi
touch "$LAST_RUN"
mkdir -p "$HERMES_DIR" "$VOICE_NOTES"

# ── Ensure sentinel exists ────────────────────────────────────
[ -f "$SENTINEL" ] || touch "$SENTINEL"

# ── Find new .m4a files in Recordings/ only (depth 1) ────────
NEW_AUDIO=()
while IFS= read -r -d '' f; do
  NEW_AUDIO+=("$f")
done < <(find "$RECORDINGS" -maxdepth 1 -name "*.m4a" -newer "$SENTINEL" -print0)

[ ${#NEW_AUDIO[@]} -eq 0 ] && exit 0

# ── Copy audio files into hermes/ (prevents re-trigger) ───────
COPIED=()
for f in "${NEW_AUDIO[@]}"; do
  dest="$HERMES_DIR/${f##*/}"
  cp "$f" "$dest"
  [ -f "$f" ] || cp "$dest" "$f"   # restore if Automator consumed it
  COPIED+=("${f##*/}")
done

exec >> "$LOGFILE" 2>&1
echo "--- [$(date)] ---"

# ── Transcribe with Buzz (whispercpp tiny model) ──────────────
# Process each new file and save as FSNote.
for AUDIO_FILE in "${COPIED[@]}"; do
  basename="${AUDIO_FILE##*/}"
  transcript_file="$HERMES_DIR/${basename%.m4a}.txt"

  # Run Buzz transcription
  "$BUZZ" -d "$HERMES_DIR" --model whispercpp tiny "$AUDIO_FILE" 2>> "$LOGFILE"

  # Read transcript; if Buzz failed, leave transcript_file empty
  TRANSCRIPT=""
  if [ -f "$transcript_file" ]; then
    TRANSCRIPT=$(cat "$transcript_file")
  else
    echo "Warning: transcription failed for ${basename}" | tee -a "$LOGFILE"
    TRANSCRIPT="[transcription unavailable]"
    touch "$transcript_file"
  fi

  # Derive date/time from the filename (Y= YYYY M= MM D= DD
  # h= HH m= MM
  # s= SS)
  BASE="${basename%.m4a}"
  BASE="${BASE%%-*}"   # strip trailing hex suffix
  if [[ "$BASE" =~ ^([0-9]{4})([0-9]{2})([0-9]{2})\ ([0-9]{2})([0-9]{2})([0-9]{2}) ]]; then
    REC_DAT="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}-${BASH_REMATCH[3]}"
    REC_TIME="${BASH_REMATCH[4]}:${BASH_REMATCH[5]}:${BASH_REMATCH[6]}"
    REC_DATETIME="${REC_DAT} at ${REC_TIME}"
  else
    REC_DATETIME="$(date '+%Y-%m-%d at %H:%M')"   # fallback
  fi

  # ── Build FSNote Markdown ────────────────────────────────
  NOTE_FILE="$VOICE_NOTES/${basename%.m4a}.md"
  cat > "$NOTE_FILE" <<FSNOTE
# Voice Memo ${basename%.m4a}

> Voice Memo recorded ${REC_DATETIME}
> Source: \`${RECORDINGS}/${basename}\`

---

${TRANSCRIPT}

---
FSNOTE

  echo "Saved note: $NOTE_FILE"

  # ── Check for "hey hermes" ───────────────────────────────
  TRANSCRIPT_LOWER=$(echo "$TRANSCRIPT" | tr '[:upper:]' '[:lower:]')
  if [[ "$TRANSCRIPT_LOWER" =~ hey\ hermes ]]; then
    INSTRUCTION=$(echo "$TRANSCRIPT" | sed -n 's/.*[Hh][Ee][Yy]\ [Hh][Ee][Rr][Mm][Ee][Ss]//p; s/^[ \t]*//' | head -1)
    if [ -n "$INSTRUCTION" ]; then
      echo "Hey Hermes detected. Invoking Hermes with: $INSTRUCTION"
      "$HERMES" chat \
        --resume "Voice Memo Instruction" \
        -Q \
        -q "Voice memo instruction: $INSTRUCTION" &
    fi
  fi
done

# ── Update sentinel ─────────────────────────────────────────
touch "$SENTINEL"
echo "Sentinel updated."

# ── Clean up work files ─────────────────────────────────
find "$HERMES_DIR" -maxdepth 1 ! -name '.*' ! -name '*.sh' -type f -delete 2>/dev/null
