#!/bin/bash
# STT Tool - Linux Setup Script
# Run this once to set up the environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== STT Tool Setup (Linux) ==="

# 1. Create venv
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/4] Virtual environment already exists."
fi

# 2. Install dependencies
echo "[2/5] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found. Installing base packages..."
    pip install sounddevice numpy scipy pynput pyperclip flet groq openai python-dotenv faster-whisper litellm
fi

# 3. Install system dependencies
echo "[3/5] Installing system dependencies (requires sudo)..."
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y xdotool xclip wl-clipboard libportaudio2 ffmpeg
elif command -v dnf &> /dev/null; then
    sudo dnf install -y xdotool xclip wl-clipboard portaudio ffmpeg
elif command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm xdotool xclip wl-clipboard portaudio ffmpeg
else
    echo "Warning: Could not detect package manager. Please manually install: xdotool, xclip, wl-clipboard, portaudio, ffmpeg"
fi

# 4. Create systemd user service
echo "[4/5] Creating systemd user service..."
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/stt-tool.service << EOF
[Unit]
Description=Speech-to-Text Tool
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/stt_daemon.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=XAUTHORITY=$HOME/.Xauthority

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable stt-tool.service

# 5. Create Desktop Shortcut
echo "[5/5] Creating Desktop shortcut..."
DESKTOP_DIR="$HOME/Desktop"
if [ -d "$HOME/Bureau" ]; then DESKTOP_DIR="$HOME/Bureau"; fi
if [ -d "$HOME/Escritorio" ]; then DESKTOP_DIR="$HOME/Escritorio"; fi

# 起動用ラッパースクリプト作成
cat > start_stt.sh << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
source venv/bin/activate
# バックグラウンド実行してログを残す
nohup python stt_daemon.py > /tmp/stt_tool.log 2>&1 &
echo "STT Tool started. Check /tmp/stt_tool.log for details."
EOF
chmod +x start_stt.sh

# .desktopファイル作成
cat > "$DESKTOP_DIR/Open-STT-Tool.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Open STT Tool
Comment=AI Speech to Text
Exec=$SCRIPT_DIR/start_stt.sh
Icon=utilities-terminal
Terminal=false
Categories=Utility;Application;
EOF
chmod +x "$DESKTOP_DIR/Open-STT-Tool.desktop"
# GNOME等で信頼済みとしてマーク（可能な場合）
gio set "$DESKTOP_DIR/Open-STT-Tool.desktop" metadata::trusted true 2>/dev/null || true

echo ""
echo "=== Setup Complete ==="
echo "To start manually: Use the 'Open STT Tool' shortcut on your Desktop"
echo "                   or run ./start_stt.sh"
echo "To check service:  systemctl --user status stt-tool.service"
echo ""
echo "The service is also registered to auto-start on login."
