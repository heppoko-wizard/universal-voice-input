# 録音フリーズバグの修正

## タスク一覧

- [x] 原因調査・ログ分析
- [x] 実装計画の作成・レビュー
- [x] バグ修正の実装
  - [x] `stt_worker_unified.py`: 録音エラー時のステータスリカバリ追加
  - [x] `stt_worker_unified.py`: config.jsonの`sample_rate`を録音で使用
  - [x] `stt_worker_unified.py`: リサンプリング処理の追加(44100Hz→16000Hz)
  - [x] `stt_daemon.py`: ワーカーのREADYステータスでデーモンの`recording`フラグをリセット
- [x] 構文チェック
- [ ] 実機での動作検証（ユーザーによる手動確認）
