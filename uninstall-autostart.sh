#!/bin/zsh
# Remove the login autostart and stop the running clock.
PLIST="$HOME/Library/LaunchAgents/com.abdun.emojiclock.plist"
launchctl bootout gui/$(id -u) "$PLIST" 2>/dev/null
rm -f "$PLIST"
pkill -f emoji_clock.py
echo "Autostart removed."
