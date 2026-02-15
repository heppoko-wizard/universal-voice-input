#!/bin/bash
cd "/home/heppo/ai_tools/speech_to_text"
source venv/bin/activate
export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib/python3.12/site-packages/nvidia/cublas/lib:$VIRTUAL_ENV/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}"
nohup python stt_daemon.py > /tmp/stt_tool.log 2>&1 &
echo "STT Tool started. Check /tmp/stt_tool.log for details."
