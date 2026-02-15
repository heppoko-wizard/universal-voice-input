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
echo "[1/5] Installing system dependencies..."
brew install portaudio ffmpeg python@3.11

# 3. Create venv
if [ ! -d "venv" ]; then
    echo "[2/5] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[2/5] Virtual environment already exists."
fi

# 4. Install Python dependencies
echo "[3/5] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found. Installing base packages..."
    pip install sounddevice numpy scipy pynput pyperclip flet groq openai python-dotenv faster-whisper litellm
fi

# 5. Create LaunchAgent for autostart
echo "[4/5] Creating LaunchAgent for autostart..."
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
        <string>$SCRIPT_DIR/stt_daemon.py</string>
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

# 6. Create double-clickable start script
echo "[5/5] Creating start_stt_gui.command..."
cat > start_stt_gui.command << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source venv/bin/activate
# バックグラウンド実行
nohup python stt_daemon.py > /tmp/stt_gui.log 2>&1 &
echo "STT Tool started in background."
EOF
chmod +x start_stt_gui.command

echo ""
echo "=== Setup Complete ==="
echo "To start manually: Double-click 'start_stt_gui.command'"
echo "To stop:           launchctl stop com.stt-tool"
echo "To view logs:      tail -f /tmp/stt-tool.log"
echo ""
echo "The service will auto-start on login."

