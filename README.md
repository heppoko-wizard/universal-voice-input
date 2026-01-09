# 🎙️ Linux Speech-to-Text Tool (v2.2)

A lightning-fast, highly accurate speech-to-text tool for Linux (X11/KDE/GNOME).  
Powered by **Groq API** (Whisper Large V3) for near-instant transcription, with seamless fallback support and a modern GUI.

---

## ✨ Features

- **🚀 Ultra Fast**: Transcription in < 0.5s via Groq's LPU.
- **⚡ Cost & Time Efficient**: **Audio Speed-Up** feature compresses audio time (default 2x) before sending, saving API costs and reducing latency.
- **🎯 High Accuracy**: Uses OpenAI's Whisper Large V3 (via Groq) or Whisper-1 (via OpenAI).
- **🎤 Auto Mic Selection**: Automatically detects and selects the active microphone with the best audio level at startup.
- **🔴 Visual Feedback**: Displays a prominent **Red Frame** overlay on screen while recording, so you never forget you're on air.
- **🖥️ Modern GUI**: Easily configure API keys, speed factor, microphone devices, and settings using a Flet-based interface.
- **🔄 Multi-API Fallback**: Automatically tries multiple APIs (Groq -> OpenAI -> etc.) if one fails.
- **⌨️ Global Hotkey**: Trigger recording with a customizable hotkey (default: `Alt+Space`).
- **📋 Smart Typing**: Pastes text via clipboard for perfect Japanese/Kanji support, then **automatically restores your original clipboard**.

---

## 🛠️ Requirements

- **OS**: Linux (X11 recommended).
- **Python**: 3.8 or higher.
- **Dependencies**: `xdotool`, `xclip`, `portaudio19-dev`, `ffmpeg`.
- **API Keys**: [Groq](https://console.groq.com/keys) (Free) and/or [OpenAI](https://platform.openai.com/).

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/heppoko-wizard/linux-groq-stt.git
cd linux-groq-stt

# Install system dependencies
sudo apt update
sudo apt install -y xdotool xclip portaudio19-dev python3-venv ffmpeg

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

Launch the settings GUI to enter your API keys and select your microphone:

```bash
./start_gui.sh
```

- **Speed Factor**: Set audio playback speed (e.g., `2.0` for 2x speed) to save costs.
- **Device**: Set to "Default" to enable **Auto Selection** at startup.

### 3. Usage

Start the background listener:

```bash
./start_stt.sh
```

- **Record**: Press `Alt` + `Space` (Start sound plays & Red Frame appears).
- **Stop**: Press `Alt` + `Space` again (Stop sound plays & Red Frame vanishes).
- **Result**: The transcribed text is typed instantly into your active window.

---

# 🎙️ Linux Speech-to-Text Tool (日本語)

Linux 向けの爆速・高精度な音声入力ツールです。  
**Groq API** (Whisper Large V3) を活用し、ほぼ遅延のない入力を実現。フォールバック機能やモダンな設定画面も備えています。

## ✨ v2.2 新機能

- **⚡ 倍速送信機能**: 録音データを自動で倍速（デフォルト2倍）に圧縮してAPIへ送信。**API料金の節約**と**レスポンス向上**を実現。
- **🎤 マイク自動選択**: 起動時に全マイクをテストし、最も音量の大きいマイクを自動で選択します（設定で「Default」選択時）。
- **🔴 録音中オーバーレイ**: 録音中は画面中央に**赤い枠**が表示されるため、録音の切り忘れを防げます。
- **⌨️ ホットキー変更**: デフォルトを `Alt + Space` に変更しました（GUIで変更可能）。

## 🚀 使い方

1. **設定**: `./start_gui.sh` を実行してAPIキーとマイクを設定。
2. **起動**: `./start_stt.sh` を実行して待機。
3. **入力**: `Alt + Space` を押して話し（赤い枠が表示されます）、もう一度押すと入力されます。

---

## 📝 License
MIT License
