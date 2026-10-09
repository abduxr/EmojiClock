#!/bin/zsh
# Start EmojiClock automatically at every login (macOS LaunchAgent).
DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.abdun.emojiclock.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.abdun.emojiclock</string>
  <key>ProgramArguments</key><array>
    <string>$DIR/.venv/bin/python</string>
    <string>$DIR/emoji_clock.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>LimitLoadToSessionType</key><string>Aqua</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/EmojiClock.log</string>
</dict></plist>
PL
launchctl bootout gui/$(id -u) "$PLIST" 2>/dev/null
launchctl bootstrap gui/$(id -u) "$PLIST" && echo "Autostart installed: $PLIST"
