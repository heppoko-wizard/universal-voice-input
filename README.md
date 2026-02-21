# Open STT Tool

**システム全体どこでも使える、完全クロスプラットフォーム（Windows / macOS / Linux Wayland対応）のローカル＆クラウド対応音声認識（Speech-to-Text）デスクトップアプリケーション。**

## 🌟 できること (Features)
- **ワンボタンで瞬時にテキスト入力**: 設定したグローバル・ホットキー（例: `Ctrl+Shift+Space`）を押して話すだけで、現在アクティブなウィンドウ（ブラウザ、エディタ、チャットアプリなど）のカーソル位置へ直接文字が「自動タイピング」されます。
- **完全ローカルでの高速・高精度な推論**:
  - `faster-whisper` エンジンを搭載し、日本語特化の `Kotoba-Whisper v2.2` や高精度な `Whisper Large v3 Turbo` などを使用可能。
  - INT8量子化によってGPU（VRAM）の消費を抑えつつ、超高速な文字起こしを実現。
- **クラウドAPI（オンライン）への切り替え設定**:
  - GPUのない低スペックPCでも、Groq APIやOpenAI APIを利用することで爆速の文字起こしが可能。
- **柔軟な録音モード**:
  - トグル（一度押して開始、もう一度押して終了）とホールド（押している間だけ録音）の両モードから自分に合ったスタイルを選択可能。
- **フローティングUI & 音声フィードバック**:
  - 作業の邪魔にならない半透明のフローティングステータスバー（表示位置は画面の上・中央・下端から選択可能）で、「録音時間（タイマー）」や「処理中」の状態を視覚的に通知。
  - 録音の開始・終了時やマイクのエラー発生時にはシステム音が鳴るため、画面を見ずにノールックでの声打ち操作に対応。
- **賢いメモリ・VRAM管理（ハイブリッドアンロード）**:
  - 【常時保持モード】最速のレスポンスを実現
  - 【0秒解放モード】録音ごとにモデルを開放しVRAMを節約（ゲームや別開発との並行に最適）
  - 【ハイブリッドモード】指定秒数だけメモリ上に待機し、使われなければ自動でアンロード
- **美しいGUI設定（Flet採用）**:
  - Fletを用いたモダンな設定画面から、「マイクデバイスの選択」「ホットキー変更」「モデルの自動ダウンロード（最適化）」まですべてがGUI操作で完結。

## 💡 特筆すべき点 (Unique Points)
- **真のクロスプラットフォームとWayland対応への執念**:
  多くのLinux用音声入力ツールが X11（レガシーなウィンドウシステム）や固有のコマンド（`xdotool` や `notify-send` 等）に依存しており Wayland 環境で動かなくなる中、当ツールは `pynput`、 `pystray`、 透過処理特化の `Tkinter` オーバーレイを活用することで、**OS固有の強引なハックなしに Linux(Wayland/X11) / Windows / macOS のすべてにおいて同一のPythonコードで完全に動作する** 非常に堅牢な設計になっています。
- **マルチプロセス化によるクラッシュフリー設計**:
  音声キャプチャと重い推論を担う（Worker）プロセスと、ユーザインタフェース・ホットキー監視を担う（Daemon）プロセスを完全に分離しています。片方が重くなったりマイクデバイスが不意に抜けても、アプリ全体がフリーズして落ちてしまうこと（デッドロック）を徹底的に防ぐ設計になっています。

## 👥 どういう人におすすめか (Who is it for?)
- **タイピングより話す方が早く、サクサク入力したい方**: 日常のメッセンジャー、コードのコメント、ブログの執筆などを「声だけ」で圧倒的な速度で入力し、腱鞘炎も予防したい方。
- **プライバシーを重視・機密情報の入力が多いビジネスパーソン**: 完全ローカルモデルを使用すれば、音声データが外部のサーバーに送信されることは一切ありません。社外秘の情報や個人的なメモの入力に最適です。
- **クロスプラットフォームで複数のPCを渡り歩くエンジニア**: WindowsのゲーミングPC、持ち運び用のMacBook、開発用のLinux（Wayland）など、どのOSでも**全く同じ操作感で自分の生産性を高めたい**パワーユーザー。

---

# Open STT Tool (English)

**A universal, cross-platform (Windows / macOS / Linux Wayland compatible) Speech-to-Text desktop application that auto-types your voice directly into any active window, completely locally.**

## 🌟 Features
- **Instant System-wide Typing**: Press your global hotkey (e.g., `Ctrl+Shift+Space`), speak, and your words are instantly "auto-typed" into whichever application you are using (browser, code editor, chat app, etc.).
- **Fast & Accurate Local Inference**:
  - Powered by `faster-whisper`. Supports highly optimized models like `Kotoba-Whisper v2.2` (for Japanese) and `Whisper Large v3 Turbo`.
  - Runs in INT8 quantization to maximize speed and minimize GPU VRAM consumption.
- **Online Cloud API Fallback**:
  - No GPU? No problem. Seamlessly switch to cloud providers like Groq or OpenAI for lightning-fast transcription on low-end hardware.
- **Flexible Hotkey Modes**:
  - Supports both **Toggle mode** (press to start, press again to stop) and **Hold mode** (record only while holding the key).
- **Floating Status Overlay & Audio Feedback**:
  - A non-intrusive, semi-transparent floating bar (position configurable: Top/Center/Bottom) displays recording timer and processing states.
  - Audio chimes notify you when recording starts/stops or if an error occurs, enabling 100% eyes-free dictation.
- **Smart Memory & VRAM Management**:
  - **Always Loaded**: Instant response times (keeps model permanently in memory).
  - **Zero Memory**: Frees the model immediately after transcription to save VRAM for other tasks.
  - **Hybrid Timeout**: Keeps the model loaded for a configurable number of seconds before unloading automatically.
- **Beautiful GUI Configuration via Flet**:
  - Comes with a sleek graphical settings editor. Download/optimize local models, change microphones, and configure global hotkeys without touching a single JSON file.

## 💡 Unique Points
- **A Truly Cross-Platform Triumph (Wayland Compatible)**:
  While many Linux dictation tools rely on legacy X11 utilities (`xdotool`, `notify-send`) and break entirely on modern Wayland systems, this tool is built from the ground up using `pynput`, `pystray`, and multi-OS transparent `Tkinter` to ensure **perfect operation across Linux (Wayland & X11), Windows, and macOS—using the exact same codebase without dirty OS hacks.**
- **Crash-Free Separation Architecture**:
  The heavy lifting of audio recording and AI inference (Worker process) is strictly separated from the system tray and hotkey monitoring (Daemon process). This dual-process architecture ensures that even if a transcription takes too long or a microphone gets unplugged suddenly, your main application will never freeze, stutter, or crash.

## 👥 Who is this for?
- **Speed Typists & Health Conscious Users**: If you want to blast through emails, code documentation, or chat messages much faster than typing, or if you're trying to prevent Repetitive Strain Injury (RSI).
- **Privacy Advocates & Enterprise Users**: By using the Fast Local Models, your voice data never leaves your machine. Perfect for dictating highly confidential work documents, NDAs, or personal journals.
- **Nomadic Power Users & Engineers**: People who work across multiple operating systems—a Windows rig, a Linux development machine, and a macOS laptop—and want the exact same reliable voice setup and productivity everywhere.
