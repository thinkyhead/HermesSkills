-- verify_folder_action.applescript
-- Verifies the Folder Action is correctly attached to the Voice Memos Recordings folder.
--
-- Authors: Thinkyhead, Hermes
-- Part of the setup-voice-memo-pipeline skill.
--
-- Expected output:
--   Folder Action on: /Users/<you>/Library/Group Containers/...
--   Scripts: UltraHD:Users:<you>:Library:Workflows:...
--   Enabled: true

set recordings_posix to (POSIX path of (path to home folder)) & "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"

tell application "System Events"
  if exists folder action recordings_posix then
    set fa to folder action recordings_posix
    set script_paths to {}
    repeat with s in every script of fa
      set end of script_paths to (path of s)
    end repeat
    set enabled_state to enabled of fa
    log "Folder Action on: " & recordings_posix
    log "Scripts: " & (script_paths as string)
    log "Enabled: " & (enabled_state as string)
  else
    log "No Folder Action found for: " & recordings_posix
  end if
end tell
