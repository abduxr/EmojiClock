# EmojiClock 🌞🌙

A tiny floating macOS widget that shows **IST + UTC** time as dancing sun/moon emojis in the top-left corner.

- Drag to move · hover to make them dance faster · right-click for 12h/24h and Quit

## Requirements
- macOS with Python 3.9+ (`python3 --version`)

## One-line install (starts now + at every login)
```zsh
git clone https://github.com/abduxr/EmojiClock.git ~/EmojiClock && cd ~/EmojiClock && ./setup.sh && ./install-autostart.sh
```

## Install & run (manual)
```zsh
git clone https://github.com/abduxr/EmojiClock.git
cd EmojiClock
./setup.sh                              # creates .venv and installs PyObjC
.venv/bin/python emoji_clock.py         # run it
```

## Start automatically at login (optional)
```zsh
./install-autostart.sh      # enable
./uninstall-autostart.sh    # disable + stop
```
