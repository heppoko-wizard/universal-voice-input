# STT起動時の録音・転写エラー 調査と対処

## 発生日: 2026-02-15

## 症状

1. Ctrl+Space で録音開始しても `Recording error: Invalid number of channels [PaErrorCode -9998]` で即座に失敗
2. 録音成功しても `Library libcublas.so.12 is not found` で転写が失敗

## 原因1: mic_checker による device_index の誤上書き

### 詳細

- `stt_daemon.py` は起動時に `mic_checker.find_working_device()` を呼び出す
- mic_checker は `preferred_index`（= `default_device_index`）に対して **`channels=1`** で録音テストを行う
- Device 3 は ALSA の `hw` デバイスであり、1ch での録音がエラーになる場合がある
- チェック失敗 → フォールバック処理で**別のデバイス（Device 5: HD-Audio Generic）**を選択
- `config.json` の `device_index` を 5 に**上書き保存**
- ワーカーは `start_recording()` で毎回 config を再読み込みするため、誤った Device 5 を使用
- Device 5 は内蔵サウンドカードのアナログ入力で、物理マイク未接続のためエラー

### 対処

`stt_daemon.py` の起動時マイクチェック呼び出しをコメントアウト:

```python
# 起動時マイクチェック（無効化: device_indexを誤って上書きする問題があるため）
# threading.Thread(target=self._startup_mic_check, daemon=True).start()
```

### 恒久対策（未実施）

- mic_checker が `channels=1` ではなくデバイスの `max_input_channels` に合わせた録音テストを行うよう修正
- フォールバック時に config を上書きせず、一時的なセッション設定として扱う

---

## 原因2: LD_LIBRARY_PATH 未設定による CUDA ライブラリ不足

### 詳細

- `faster-whisper` は GPU 推論に `libcublas.so.12` を必要とする
- このライブラリは pip でインストールされた `nvidia-cublas-cu12` パッケージ内に存在:
  `venv/lib/python3.12/site-packages/nvidia/cublas/lib/libcublas.so.12`
- しかし `LD_LIBRARY_PATH` が設定されていないため、ランタイムリンカーが見つけられない

### 対処

`start_stt.sh` に `LD_LIBRARY_PATH` を追加:

```bash
export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib/python3.12/site-packages/nvidia/cublas/lib:$VIRTUAL_ENV/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}"
```

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `stt_daemon.py` | mic_checker の起動時呼び出しを無効化 |
| `start_stt.sh` | `LD_LIBRARY_PATH` にNVIDIA CUDAライブラリパスを追加 |
| `config.json` | `device_index=4`, `default_device_index=4` に修正（gitignore対象） |
