---
name: fsnotes
description: Read, search, create, and edit notes in FSNotes on macOS. Notes are plain Markdown files or .textbundle directories stored in iCloud and synced across devices.
tags: [notes, markdown, fsnotes, macos, icloud]
related_skills: [apple-notes, obsidian]
platforms: [macos]
---

# FSNotes

FSNotes stores notes as plain files on disk — no CLI required. Read, write, and search them directly. Changes sync automatically via iCloud.

## Storage Location

Base path:
  ~/Library/Mobile Documents/iCloud~co~fluder~fsnotes/Documents/

Shell variable for convenience (use in all commands):
  FSNOTES="$HOME/Library/Mobile Documents/iCloud~co~fluder~fsnotes/Documents"

## Note Formats

Two formats coexist in the same directory:

1. **Plain Markdown:** `NoteTitle.md`
   - Single file, read/write directly.

2. **TextBundle:** `NoteTitle.textbundle/` (directory)
   - `text.markdown` — the note content (read/write this file)
   - `info.json` — metadata (type, version, creatorIdentifier)
   - May also contain an `assets/` subfolder for attachments.

## Folders / Notebooks

Subfolders inside the base path are notebooks in FSNotes. Notes inside subfolders follow the same `.md` / `.textbundle` format.

The Trash folder is at:
  ~/Library/Mobile Documents/iCloud~co~fluder~fsnotes/Documents/Trash/

## Operations

### List all notes
```bash
find "$FSNOTES" -not -path "*/Trash/*" \
  \( -name "*.md" -o -name "*.textbundle" \) | sort
```

### List notes in a specific folder
```bash
ls "$FSNOTES/FolderName/"
```

### Read a plain `.md` note
```python
read_file("$FSNOTES/NoteTitle.md")
```

### Read a `.textbundle` note
```python
read_file("$FSNOTES/NoteTitle.textbundle/text.markdown")
```

### Search notes by content
```python
# For plain .md files:
search_files(pattern="search term", path="$FSNOTES", file_glob="*.md")

# For textbundles:
search_files(pattern="search term", path="$FSNOTES", file_glob="*.markdown")
```

### Create a new plain `.md` note (preferred)
```python
write_file("$FSNOTES/NoteTitle.md", "# NoteTitle\n\ncontent here")
```
Appears in FSNotes immediately; iCloud syncs to other devices.

**Verification:** Always verify the write succeeded by checking the file exists:
```python
import os
file_path = "$FSNOTES/NoteTitle.md"
if os.path.exists(file_path):
    print("✅ Write verified")
else:
    # Retry with direct Python file write if tool's write failed silently
    with open(file_path, "w") as f:
        f.write(content)
```

### Create a note in a folder/notebook
```python
write_file("$FSNOTES/FolderName/NoteTitle.md", "# NoteTitle\n\ncontent")
```

**Verification:** Check file exists after write to catch silent failures.

### Create a new `.textbundle` note
1. `terminal(command="mkdir '$FSNOTES/NoteTitle.textbundle'")`
2. `write_file(".../NoteTitle.textbundle/text.markdown", "# NoteTitle\n\ncontent")`
3. `write_file(".../NoteTitle.textbundle/info.json", '{
     "type": "net.daringfireball.markdown",
     "creatorIdentifier": "co.fluder.fsnotes",
     "version": 2,
     "flatExtension": "markdown"
   }')`

Note: prefer plain `.md` unless you need attachments.

### Edit a note
```python
# For targeted edits:
patch(path="$FSNOTES/NoteTitle.md", old_string="...", new_string="...")

# For full rewrites:
write_file("$FSNOTES/NoteTitle.md", full_new_content)
```

### Delete a note (move to Trash)
```bash
terminal(command="mv '$FSNOTES/NoteTitle.md' '$FSNOTES/Trash/'")
```

### Open a note in FSNotes.app
```bash
terminal(command="open -a FSNotes '$FSNOTES/NoteTitle.md'")
```

## Transferring Notes from Apple Notes

Apple Notes returns HTML via AppleScript. Convert to Markdown before writing:

1. **Fetch the note body:**
   ```bash
   osascript -e 'tell application "Notes" to return body of (first note whose name is "Title")'
   ```

2. **Convert HTML to Markdown** with a Python snippet:
   - `h1/h2/h3` → `#/##/###`
   - `<b>` → `**bold**`
   - `<tt>` → `` `code` ``
   - `<a href="...">` → `[text](url)`
   - `<li>` → `- list item`
   - Strip all remaining tags
   - Decode `&gt;`, `&lt;`, `&amp;` entities
   - Collapse 3+ blank lines to 2
   - Remove empty headings (`##` with no text)

3. **Write to FSNotes:**
   ```python
   write_file("$FSNOTES/Note Title.md", markdown_content)
   ```

## Tags

Tags are written inline in note content as `#tagname` — FSNotes parses them automatically from the Markdown.

## TODO System (Common Convention)

Many users employ FSNotes as a cross-project TODO system:

- **Format:** Markdown checkboxes — `- [ ]` pending, `- [x]` done
- **Per-project:** Each active project has a `## TODO` section in its note, or a standalone `ProjectName TODO.md`
- **Master index:** `TODO Index.md` at the FSNotes root links to all active project todo lists
- **Time-sensitive escalation:** Urgent or deadline-driven items get promoted to Apple Reminders (see `apple-reminders` skill)

When adding a todo, put it in the relevant project note under `## TODO`. If no project note exists yet, create one. Update `TODO Index.md` if the project is new.

## Pitfalls

- **iCloud container access from CLI may fail** due to macOS privacy entitlements.
  If this occurs, check the reference document at `references/icloud-access-failure.md`.
- The base path contains a space ("Mobile Documents") — always quote it in shell commands.
- `.textbundle` is a directory, not a file — read `text.markdown` inside it, not the bundle itself.
- Don't write to the Trash folder.
- FSNotes picks up file changes immediately — no app restart needed.
- iCloud sync may have a short delay on other devices.
- **Search Pattern Regex:** `search_files` uses regex patterns, so special characters like `]`, `(`, `/` must be escaped. To search for `](//`, use pattern `r'\\]\\(//'`.
