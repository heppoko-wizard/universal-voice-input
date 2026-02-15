# 録音フリーズバグ修正 - ウォークスルー

## 修正概要

録音開始ショートカットを押すと赤枠が表示されたままフリーズするバグを修正。

## 根本原因

1. **サンプルレート不整合**: `config.json`の`sample_rate: 44100`がワーカーに無視され、ハードコード値`16000`でALSAストリームを開こうとしてエラー
2. **エラー時のステータス未復帰**: 録音エラー後に`[STATUS] READY`が出力されず、オーバーレイ赤枠が残りデーモンのトグル状態もロック

## 変更ファイル

### [stt_worker_unified.py](file:///home/heppo/ai_tools/speech_to_text/stt_worker_unified.py)

render_diffs(file:///home/heppo/ai_tools/speech_to_text/stt_worker_unified.py)

| 変更 | 内容 |
|---|---|
| 定数リネーム | `SAMPLE_RATE` → `DEFAULT_SAMPLE_RATE` + `INFERENCE_SAMPLE_RATE` |
| configの`sample_rate`使用 | `_record_loop()`でconfigのsample_rateでストリームを開く |
| エラーリカバリ | 録音例外時に`[STATUS] READY`を出力して赤枠を解除 |
| リサンプリング | 録音44100Hz→推論16000Hzへの変換を`scipy.signal.resample`で追加 |
| WAVヘッダ修正 | オンラインAPI送信時のframerateを`INFERENCE_SAMPLE_RATE`で正確に設定 |

### [stt_daemon.py](file:///home/heppo/ai_tools/speech_to_text/stt_daemon.py)

render_diffs(file:///home/heppo/ai_tools/speech_to_text/stt_daemon.py)

`on_worker_status()`にREADY受信時の`self.recording = False`を追加し、トグルのデッドロックを防止。

## 検証結果

- ✅ `stt_worker_unified.py` 構文チェック通過
- ✅ `stt_daemon.py` 構文チェック通過
- ✅ `scipy` は `requirements.txt` に記載済み、venvにインストール済み (v1.16.3)
- ⬜ 実機での録音テストはユーザーによる手動確認が必要
