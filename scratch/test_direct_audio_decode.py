import base64
import io
import os
import sys
import time
import wave
import json
import numpy as np

sys.path.append(os.path.abspath('2_Edge_Server_AI'))
sys.path.append(os.path.abspath('2_Edge_Server_AI/navigation_module'))

from mobile_5g_bridge import MobileBridgeServer
from speech_to_text import transcribe_audio_np

# Read captured_voice_debug.wav
with open('captured_voice_debug.wav', 'rb') as f:
    raw_wav = f.read()

with wave.open(io.BytesIO(raw_wav), 'rb') as wf:
    framerate = wf.getframerate()
    pcm_data = wf.readframes(wf.getnframes())
    audio_np = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0

if framerate != 16000:
    target_len = int(len(audio_np) * 16000 / framerate)
    audio_np = np.interp(
        np.linspace(0, len(audio_np), target_len, endpoint=False),
        np.arange(len(audio_np)),
        audio_np
    ).astype(np.float32)

# Pack as standard 16kHz WAV base64 like phone's encodeWAV does
bio = io.BytesIO()
with wave.open(bio, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes((np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16).tobytes())

b64_str = base64.b64encode(bio.getvalue()).decode('utf-8')

# Now run the exact decode logic from mobile_5g_bridge.py
raw_bytes = base64.b64decode(b64_str)
decoded_audio = None
with wave.open(io.BytesIO(raw_bytes), "rb") as wf:
    fr = wf.getframerate()
    nf = wf.getnframes()
    pcm = wf.readframes(nf)
decoded_audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

print(f"Decoded {len(decoded_audio)} samples at {fr}Hz successfully!")
assert len(decoded_audio) > 0, "Decoded audio is empty!"

# Run Whisper AI
dest = transcribe_audio_np(decoded_audio)
print(f"Whisper Transcription Result: [{dest}]")
assert dest is not None, "Whisper transcription returned None!"
print("🎉 ALL CHECKS PASSED PERFECTLY!")
