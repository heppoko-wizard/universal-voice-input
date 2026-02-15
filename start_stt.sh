#!/bin/bash
cd "/home/heppo/ai_tools/speech_to_text"
source venv/bin/activate
nohup python stt_daemon.py > /tmp/stt_tool.log 2>&1 &
echo "STT Tool started. Check /tmp/stt_tool.log for details."
