# 🎙️ Cross-Platform AI Speech-to-Text Tool (v3.0)

A lightning-fast, highly accurate speech-to-text tool for **Linux, macOS, and Windows**.  
Supports **Local Inference** (running offline on your GPU/CPU) and **Cloud APIs** (Groq/OpenAI), giving you the best of both worlds.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.8%2B-blue)

---

## ✨ Key Features

- **🚀 Dual Mode Inference**:
  - **Local Mode (New)**: Runs offline using `Faster-Whisper` (CTranslate2). Zero latency, zero cost.
  - **Cloud Mode**: Powered by **Groq API** (Whisper Large V3) for ultra-fast cloud transcription.
  
- **🎮 GPU & Memory Optimization**:
  - **GPU Acceleration**: Utilizes CUDA (NVIDIA) with Float16 quantization for blazing speeds.
  - **Transient Mode**: Automatically unloads the model from VRAM after transcription to free up resources for games or Stable Diffusion.
  - **RAM Cache**: Keeps model files in system RAM for instant loading, even when "Transient Mode" is active.

- **🖥️ Cross-Platform**:
  - **Linux**: X11/Wayland support, systemd service integration.
  - **Windows**: Background task, startup shortcut.
  - **macOS**: LaunchAgent support.

- **🎤 Smart Features**:
  - **Auto Mic Selection**: Detects the best active microphone.
  - **Visual Overlay**: Displays a "Recording" indicator (Linux only).
  - **Global Hotkey**: Customizable trigger (default: `Ctrl+Shift+Space`).
  - **Smart Typing**: Pastes text via clipboard for perfect Japanese/Kanji support.

---

## 🛠️ Requirements

- **Python**: 3.10 or higher.
- **FFmpeg**: Required for audio processing.
- **NVIDIA GPU (Optional)**: For local acceleration (requires CUDA Toolkit 12+).

---

## 🚀 Installation

### 1. Clone & Setup

Download the repository and run the setup script for your OS.

#### 🐧 Linux

```bash
git clone https://github.com/heppoko-wizard/linux-groq-stt.git
cd linux-groq-stt
chmod +x setup_linux.sh
./setup_linux.sh
```

#### 🍎 macOS

```bash
git clone https://github.com/heppoko-wizard/linux-groq-stt.git
cd linux-groq-stt
chmod +x setup_macos.sh
./setup_macos.sh
```

#### 🪟 Windows

Run `setup_windows.ps1` as Administrator in PowerShell:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\setup_windows.ps1
```

---

## ⚙️ Configuration

Launch the GUI settings manager:

```bash
# Linux / macOS
./start_gui.sh

# Windows
.\start_gui.bat
```

### Recommended Settings

| Feature | Setting | Description |
| :--- | :--- | :--- |
| **Local Inference** | `ON` | Use offline model (Faster-Whisper). |
| **Inference Device** | `GPU (CUDA)` | Select GPU for speed. (Use CPU if no GPU) |
| **Keep Model Loaded** | `OFF` | **Unloads VRAM** after use. Great for gamers/AI artists. |
| **Force RAM Cache** | `ON` | Keeps files in RAM. **Eliminates load time** when "Keep Model Loaded" is OFF. |

---

## 🎤 Usage

The tool runs in the background.

1. **Start Recording**: Press `Ctrl` + `Shift` + `Space` (Customizable).
   - A sound will play indicating recording started.
2. **Speak**: Speak naturally.
3. **Stop Recording**: Press the hotkey again.
   - Processing sound plays.
   - Text is typed into your active window.

---

## 🧩 Advanced: Memory Management strategy

If you want to use **Stable Diffusion** or play **Heavy Games** while using STT, use this configuration:

1. **Keep Model Loaded (VRAM)**: `OFF` -> VRAM is empty when not talking.
2. **Force RAM Cache**: `ON` -> System RAM holds the model data.
3. **Prepare Model**: The system pre-loads the model *while you are speaking*.

**Result**: Zero impact on GPU performance while gaming, but instant transcription when needed.

---

## 📝 License

MIT License
