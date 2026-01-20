#!/bin/bash
# STT Coreプロセスを終了するスクリプト

echo "STT Coreプロセスを検索中..."
PID=$(pgrep -f "python -u core.py")

if [ -z "$PID" ]; then
    echo "STT Coreプロセスが見つかりません。"
    exit 0
fi

echo "PID $PID を終了します..."
kill $PID

sleep 1

# 確認
if pgrep -f "python -u core.py" > /dev/null; then
    echo "通常終了に失敗しました。強制終了します..."
    pkill -9 -f "python -u core.py"
    sleep 1
fi

if pgrep -f "python -u core.py" > /dev/null; then
    echo "❌ プロセスの終了に失敗しました。"
    exit 1
else
    echo "✅ STT Coreプロセスを終了しました。"
    exit 0
fi
