# iCloud Access Failure Resolution

## Problem

On macOS, the CLI may fail to access the FSNotes iCloud container due to privacy entitlements:

```
Error: Permission denied or cannot access path
```

## Solution

Use the `asuser` command to run commands as the logged-in user:

```bash
# Get the UID of the logged-in user (usually 501)
USER_UID=$(id -u)

# Run commands as that user
launchctl asuser $USER_UID /bin/bash -c "your-command-here"

# Example:
launchctl asuser 501 ls ~/Library/Mobile\ Documents/
```

## Verification

Test access before running full operations:

```bash
launchctl asuser 501 test -d ~/Library/Mobile\ Documents/iCloud~co~fluder~fsnotes/Documents && echo "Access OK" || echo "Access denied"
```

## Notes

- The UID is typically `501` for the first user account on macOS
- Use `id -u` to get your specific UID if different
- This workaround is needed because CLI tools run as root/system, not the logged-in user
