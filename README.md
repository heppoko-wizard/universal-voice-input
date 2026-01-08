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

---

# Linux Speech-to-Text Tool (日本語)

Linux (Kubuntu/KDEで動作確認済み) 向けの、爆速かつ高精度な音声入力ツールです。  
**Groq API** (Whisper Large V3) を使用することで、ほぼ遅延のない文字起こしを実現し、アクティブなウィンドウに自動入力します。

## 特徴

- **グローバルホットキー**: `Ctrl` + `Alt` + `Space` で録音開始/停止。
- **爆速**: GroqのLPUを使用し、0.5秒以下で文字起こし完了。
- **高精度**: OpenAIのWhisper Large V3モデルを採用。
- **スマート入力**: クリップボード経由で貼り付けるため、日本語（漢字）も文字化けせず完璧に入力されます。入力後は**元のクリップボードの内容を自動復元**します。
- **マイク自動検出**: "Blue Yeti" マイクを優先的に検出して使用します（設定可）。

## 動作要件

- Linux (X11環境推奨) - Wayland環境では `xdotool` が動作しないため工夫が必要です。
- Python 3.8以上
- [Groq API キー](https://console.groq.com/keys) (現在Beta版で無料利用可能)。
- システムパッケージ: `xdotool`, `xclip`, `portaudio19-dev`

## インストール方法

1. **リポジトリをクローン**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/linux-groq-stt.git
   cd linux-groq-stt
   ```

2. **システムパッケージのインストール**:
   ```bash
   sudo apt update
   sudo apt install -y xdotool xclip portaudio19-dev python3-venv
   ```

3. **Python環境のセットアップ**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **APIキーの設定**:
   プロジェクトルートに `.env` ファイルを作成します:
   ```bash
   cp .env.example .env
   # .env を編集し、APIキーを貼り付けてください: GROQ_API_KEY=gsk_...
   ```

## 使い方

1. **スクリプトを実行**:
   ```bash
   ./start_stt.sh
   ```
   
2. **音声入力**:
   - 入力したい場所（エディタ、ブラウザ、Slackなど）をクリックしてフォーカスします。
   - **`Ctrl` + `Alt` + `Space`** を押します（開始音が鳴ります）。
   - 話します。
   - もう一度 **`Ctrl` + `Alt` + `Space`** を押します（終了音が鳴ります）。
   - 文字が魔法のように入力されます！

## 設定変更

`groq_stt.py` を編集してカスタマイズできます:
- **ホットキー**: `<ctrl>+<alt>+<space>` の部分を変更。
- **マイク**: 別のマイクを使う場合は `get_blue_yeti_device_id` や `SAMPLE_RATE` の値を調整してください。

## ライセンス

MIT License
