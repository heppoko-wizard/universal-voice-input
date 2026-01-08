# Linux Speech-to-Text Tool (Groq API)

A lightning-fast, highly accurate speech-to-text tool for Linux (tested on Kubuntu/KDE).  
It uses the **Groq API** (Whisper Large V3) for near-instant transcription and types the result into any active window.

## Features

- **Global Hotkey**: Press `Ctrl` + `Alt` + `Space` to record, release (toggle) to transcribe.
- **Ultra Fast**: Powered by Groq's LPU, transcription takes < 0.5s.
- **High Accuracy**: Uses OpenAI's Whisper Large V3 model.
- **Smart Input**: Pastes text via clipboard to handle Japanese/Kanji perfectly, then **restores your original clipboard**.
- **Hardware Aware**: Automatically detects "Blue Yeti" microphones (configurable).

## Requirements

- Linux (X11) - Wayland support is experimental/limited (requires `xdotool` alternative).
- Python 3.8+
- A [Groq API Key](https://console.groq.com/keys) (Free Beta available).
- System packages: `xdotool`, `xclip`, `portaudio19-dev`

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/linux-groq-stt.git
   cd linux-groq-stt
   ```

2. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y xdotool xclip portaudio19-dev python3-venv
   ```

3. **Setup Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure API Key**:
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   # Edit .env and add your key: GROQ_API_KEY=gsk_...
   ```

## Usage

1. **Run the script**:
   ```bash
   ./start_stt.sh
   ```
   
2. **Dictate**:
   - Focus on any text field (Text Editor, Browser, Slack, etc.).
   - Press **`Ctrl` + `Alt` + `Space`**. (You'll hear a start sound).
   - Speak.
   - Press **`Ctrl` + `Alt` + `Space`** again. (You'll hear a stop sound).
   - The text will magically appear!

## Configuration

Edit `groq_stt.py` to change:
- **Hotkey**: Search for `<ctrl>+<alt>+<space>`.
- **Microphone**: Modify `get_blue_yeti_device_id` or `SAMPLE_RATE` if you use a different mic.

## License

MIT License
