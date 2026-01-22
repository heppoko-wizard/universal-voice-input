# STT動作不全の解消および最適化プラン

現状、アプリケーションが「ちゃんと動かない」原因として、以下の3点が特定されました。

1. **通知の重複（スタック）**: 「Zero Memory」モードにおいて、デーモンがワーカーから返された新しい通知IDを受け取っていないため、実行のたびに新しい通知が作成され、画面を埋め尽くしています。
2. **動作の遅延（オーバーヘッド）**: 現在「Zero Memory」モードで動作しており、ホットキーを押すたびに巨大なモデル（Kotoba-Whisper）をゼロからVRAMに読み込んでいます。これには10秒〜数十秒の時間がかかり、ユーザー体験を損なっています。
3. **プロセスのハング**: 現在 PID 5562 のワーカープロセスが5分以上 CPU 100% 超で動作し続けており、文字起こしが終わらない（またはハングしている）状態です。

## 修正内容

### 1. デーモンの通知管理の修正

`stt_daemon.py` を修正し、「Zero Memory」モードでもワーカーの出力を監視して `notification_id` を更新するようにします。これにより、同じ通知が上書きされるようになります。

### 2. 推奨設定の変更（Hybridモードへの切り替え）

現在の設定では毎回モデルをロードするため非常に遅いです。`hybrid_mode` を有効にすることを提案します。これにより、一度ロードしたモデルは一定時間（デフォルト300秒）VRAMに保持され、次回以降の文字起こしが瞬時に（0.1秒程度）開始されます。

### 3. プロセスのクリーンアップ

現在ハングしていると思われるプロセスを一度強制終了し、クリーンな状態で再起動します。

## Proposed Changes

### [Component: Daemon]

#### [MODIFY] [stt_daemon.py](file:///home/heppo/ai_tools/speech_to_text/stt_daemon.py)

- `_handle_oneshot_mode` 内で `_monitor_worker_output` スレッドを開始するように修正。
- ワーカーが出力する `STT_NOTIFICATION_ID` をキャプチャし、デーモン側で保持するように修正。

### [Component: Config]

#### [MODIFY] [config.json](file:///home/heppo/ai_tools/speech_to_text/config.json)

- `hybrid_mode` を `true` に設定（ユーザーの承認後）。

## Verification Plan

### Automated Tests

- `python stt_daemon.py` を起動し、ホットキーを押して、通知が1つだけ表示・更新されることを確認。
- 2回目のホットキー入力で、モデルのリロードが発生せず、即座に「Recording」に切り替わることを確認（Hybridモード）。

### Manual Verification

- ユーザーにホットキーの挙動が改善されたか（速くなったか、通知が重ならないか）を確認してもらう。
