import sys, os
sys.path.insert(0, os.getcwd())
import wave
import numpy as np
from edge_server.navigation.speech_to_text import get_whisper_model, clean_destination_query
from edge_server.navigation.campus_snapping import snap_to_campus_landmark

whisper = get_whisper_model()
with wave.open('captured_voice_debug.wav', 'rb') as wf:
    framerate = wf.getframerate()
    frames = wf.readframes(wf.getnframes())
    audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

print(f"WAV length: {len(audio_np)/framerate:.2f}s, rate: {framerate}Hz, peak: {np.max(np.abs(audio_np)):.3f}")

segments, info = whisper.transcribe(audio_np, language='en')
raw_text = ' '.join([s.text for s in segments]).strip()
print(f"Whisper raw transcription: '{raw_text}'")
cleaned = clean_destination_query(raw_text)
print(f"Cleaned query: '{cleaned}'")
snapped, conf, corrected = snap_to_campus_landmark(cleaned or raw_text)
print(f"Snapped: '{snapped}' ({conf}%)")
