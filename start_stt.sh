#!/bin/bash
cd ~/ai_tools/speech_to_text
source venv/bin/activate
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(python3 -c 'import site; print(site.getsitepackages()[0])')/nvidia/cublas/lib:$(python3 -c 'import site; print(site.getsitepackages()[0])')/nvidia/cudnn/lib

# 既存のプロセスがあれば停止（二重起動防止 & ゾンビプロセス対策）
echo "Stopping existing processes..."
pkill -f "python -u stt_daemon.py" 2>/dev/null
pkill -f "python.*stt_worker_unified.py" 2>/dev/null
pkill -f "python.*status_overlay.py" 2>/dev/null

# 少し待つ
sleep 1

echo "Starting STT Daemon in background..."
nohup python -u stt_daemon.py > nohup.out 2>&1 &

echo "STT Daemon started (PID: $!). Check nohup.out for logs."
echo "You can close this terminal safely."