# 🎙️ Linux Speech-to-Text Tool (v2.0)

A lightning-fast, highly accurate speech-to-text tool for Linux (X11/KDE/GNOME).  
Powered by **Groq API** (Whisper Large V3) for near-instant transcription, with seamless fallback support and a modern GUI.

---

## ✨ Features

- **🚀 Ultra Fast**: Transcription in < 0.5s via Groq's LPU.
- **🎯 High Accuracy**: Uses OpenAI's Whisper Large V3 (via Groq) or Whisper-1 (via OpenAI).
- **🖥️ Modern GUI**: Easily configure API keys, microphone devices, and settings using a Flet-based interface.
- **🔄 Multi-API Fallback**: Automatically tries multiple APIs (Groq -> OpenAI -> etc.) if one fails.
- **⌨️ Global Hotkey**: Trigger recording with a customizable hotkey (default: `Ctrl+Alt+Space`).
- **📋 Smart Typing**: Pastes text via clipboard for perfect Japanese/Kanji support, then **automatically restores your original clipboard**.
- **🌐 Cross-Platform Core**: Designed with portability in mind.

---

## 🛠️ Requirements

- **OS**: Linux (X11 recommended).
- **Python**: 3.8 or higher.
- **Dependencies**: `xdotool`, `xclip`, `portaudio19-dev`.
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
sudo apt install -y xdotool xclip portaudio19-dev python3-venv

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

### 3. Usage

Start the background listener:

```bash
./start_stt.sh
```

- **Record**: Press `Ctrl` + `Alt` + `Space` (Start sound plays).
- **Stop**: Press `Ctrl` + `Alt` + `Space` again (Stop sound plays).
- **Result**: The transcribed text is typed instantly into your active window.

---

# 🎙️ Linux Speech-to-Text Tool (日本語)

Linux 向けの爆速・高精度な音声入力ツールです。  
**Groq API** (Whisper Large V3) を活用し、ほぼ遅延のない入力を実現。フォールバック機能やモダンな設定画面も備えています。

## ✨ 主な機能

- **🚀 爆速転送**: Groq LPUにより、喋り終わってから0.5秒以内に文字化。
- **🎯 最高峰の精度**: OpenAI Whisper Large V3 モデルを採用。
- **🖥️ 設定用GUI**: マイクの選択やAPIキーの管理をモダンな画面で行えます。
- **🔄 フォールバック**: Groqが落ちていてもOpenAI等へ自動で切り替えて試行。
- **⌨️ グローバルホットキー**: `Ctrl+Alt+Space` でどこでも即座に録音開始。
- **📋 クリップボード復元**: 日本語入力を確実にするためクリップボードを使用しますが、入力後は**元のクリップボード内容を自動で復元**します。

## 🚀 使い方

1. **設定**: `./start_gui.sh` を実行してAPIキーとマイクを設定。
2. **起動**: `./start_stt.sh` を実行して待機。
3. **入力**: `Ctrl+Alt+Space` を押して話し、もう一度押すと入力されます。

---

## 📝 License
MIT License