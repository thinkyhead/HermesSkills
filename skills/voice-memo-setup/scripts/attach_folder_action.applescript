-- attach_folder_action.applescript
-- Attaches the "Transcribe Voice Memos" Folder Action workflow to the
-- Voice Memos Recordings folder via System Events.
--
-- Authors: Thinkyhead, Hermes
-- Part of the setup-voice-memo-pipeline skill.
--
-- PITFALL: System Events requires the workflow path in HFS (colon-separated)
-- format, not POSIX. Convert with `POSIX file "..." as alias` first.

set recordings_posix to (POSIX path of (path to home folder)) & "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
set workflow_posix to (POSIX path of (path to home folder)) & "Library/Workflows/Applications/Folder Actions/Transcribe Voice Memos.workflow"

tell application "System Events"
  set folder_actions enabled to true

  -- Convert paths to aliases (required for System Events)
  set folder_alias to POSIX file recordings_posix as alias
  set workflow_alias to POSIX file workflow_posix as alias
  -- HFS path (colon-delimited) for make new script
  set wf_hfs to workflow_alias as string

  -- Create or reuse the folder action
  if not (exists folder action recordings_posix) then
    set fa to make new folder action at folder_alias with properties {name: recordings_posix}
  else
    set fa to folder action recordings_posix
  end if

  -- Attach the workflow script if not already attached
  set existing_scripts to every script of fa
  set already_attached to false
  repeat with s in existing_scripts
    if path of s is wf_hfs then
      set already_attached to true
      exit repeat
    end if
  end repeat

  if not already_attached then
    make new script at fa with properties {path: wf_hfs}
    log "Folder Action attached."
  else
    log "Folder Action already attached — no change."
  end if

  set enabled of fa to true
end tell
