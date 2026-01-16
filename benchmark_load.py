import time
from faster_whisper import WhisperModel
import os

model_id = "kotoba-tech/kotoba-whisper-v1.0-faster"

print(f"Benchmarking load time for {model_id}...")

# 1st Load (Cold)
start = time.time()
model = WhisperModel(model_id, device="cpu", compute_type="int8")
end = time.time()
print(f"Cold Load Time: {end - start:.4f} seconds")
del model

# 2nd Load (Warm)
start = time.time()
model = WhisperModel(model_id, device="cpu", compute_type="int8")
end = time.time()
print(f"Warm Load Time: {end - start:.4f} seconds")
del model
