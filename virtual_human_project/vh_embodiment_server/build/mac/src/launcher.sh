#!/bin/bash
APP="$(cd "$(dirname "$0")/../.." && pwd)"
# A downloaded (quarantined) app runs from a random read-only copy (App Translocation),
# where the course repository around it cannot be found. Unquarantine the original and relaunch it.
case "$APP" in
  */AppTranslocation/*)
    alert() { /usr/bin/osascript -e 'on run argv' -e 'display alert (item 1 of argv) message (item 2 of argv) as critical' -e 'end run' "$1" "$2" >/dev/null 2>&1; }
    CHOSEN="$(/usr/bin/osascript -e 'POSIX path of (choose folder with prompt "macOS opened the installer from a temporary copy. Select the course folder you downloaded (the one that contains virtual_human_project)." default location (path to downloads folder))' 2>/dev/null)" || exit 0
    ORIGINAL=""
    DIR="${CHOSEN%/}"
    while [ -n "$DIR" ]; do
      if [ -d "$DIR/virtual_human_project/vh_embodiment_server/dist/mac/Install Virtual Human.app" ]; then
        ORIGINAL="$DIR/virtual_human_project/vh_embodiment_server/dist/mac/Install Virtual Human.app"; break
      fi
      PARENT="$(dirname "$DIR")"
      [ "$PARENT" = "$DIR" ] && break
      DIR="$PARENT"
    done
    if [ -z "$ORIGINAL" ]; then
      alert 'Course folder not found' 'Select the downloaded course folder that contains virtual_human_project, with Install Virtual Human.app extracted in virtual_human_project/vh_embodiment_server/dist/mac.'
      exit 1
    fi
    if ! /usr/bin/xattr -dr com.apple.quarantine "$ORIGINAL"; then
      alert 'Could not prepare the installer' "Open Terminal and run: xattr -dr com.apple.quarantine \"$ORIGINAL\" then open the installer again."
      exit 1
    fi
    exec /usr/bin/open -n "$ORIGINAL";;
esac
exec /usr/bin/open -a Terminal "$APP/Contents/Resources/Install.command"
