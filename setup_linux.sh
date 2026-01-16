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
echo "[2/4] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install sounddevice numpy scipy pynput pyperclip flet groq openai python-dotenv faster-whisper

# 3. Install system dependencies
echo "[3/4] Installing system dependencies (requires sudo)..."
if command -v apt &> /dev/null; then
    sudo apt install -y xdotool xclip wl-clipboard libportaudio2
elif command -v dnf &> /dev/null; then
    sudo dnf install -y xdotool xclip wl-clipboard portaudio
elif command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm xdotool xclip wl-clipboard portaudio
else
    echo "Warning: Could not detect package manager. Please install xdotool, xclip, wl-clipboard, and portaudio manually."
fi

# 4. Create systemd user service
echo "[4/4] Creating systemd user service..."
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/stt-tool.service << EOF
[Unit]
Description=Speech-to-Text Tool
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/core.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable stt-tool.service

echo ""
echo "=== Setup Complete ==="
echo "To start the service now:  systemctl --user start stt-tool.service"
echo "To check status:           systemctl --user status stt-tool.service"
echo "To view logs:              journalctl --user -u stt-tool.service -f"
echo ""
echo "The service will auto-start on login."
