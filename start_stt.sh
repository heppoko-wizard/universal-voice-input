#!/bin/bash
cd ~/ai_tools/speech_to_text
source venv/bin/activate
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(python3 -c 'import site; print(site.getsitepackages()[0])')/nvidia/cublas/lib:$(python3 -c 'import site; print(site.getsitepackages()[0])')/nvidia/cudnn/lib
python stt_daemon.py