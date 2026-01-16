#!/bin/bash
# STT Tool - macOS Setup Script
# Run this once to set up the environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== STT Tool Setup (macOS) ==="

# 1. Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Install system dependencies
echo "[1/4] Installing system dependencies..."
brew install portaudio python@3.11

# 3. Create venv
if [ ! -d "venv" ]; then
    echo "[2/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[2/4] Virtual environment already exists."
fi

# 4. Install Python dependencies
echo "[3/4] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install sounddevice numpy scipy pynput pyperclip flet groq openai python-dotenv faster-whisper

# 5. Create LaunchAgent for autostart
echo "[4/4] Creating LaunchAgent for autostart..."
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.stt-tool.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.stt-tool</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/venv/bin/python</string>
        <string>$SCRIPT_DIR/core.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/stt-tool.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/stt-tool.err</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.stt-tool.plist 2>/dev/null || true

echo ""
echo "=== Setup Complete ==="
echo "To start now:    launchctl start com.stt-tool"
echo "To stop:         launchctl stop com.stt-tool"
echo "To view logs:    tail -f /tmp/stt-tool.log"
echo ""
echo "The service will auto-start on login."
