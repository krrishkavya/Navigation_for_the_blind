import asyncio
import base64
import io
import os
import sys
import time
import wave
import json
import websockets
import numpy as np

sys.stdout.reconfigure(line_buffering=True)
sys.path.append(os.path.abspath('2_Edge_Server_AI'))
sys.path.append(os.path.abspath('2_Edge_Server_AI/navigation_module'))
from mobile_5g_bridge import MobileBridgeServer

print("Starting MobileBridgeServer on 8092...", flush=True)
bridge = MobileBridgeServer(port=8092)
bridge.start()
time.sleep(1.0)

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

pcm_16k = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
bio = io.BytesIO()
with wave.open(bio, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(pcm_16k)

b64_audio = base64.b64encode(bio.getvalue()).decode('utf-8')
print(f'Prepared 16kHz WAV test payload: {len(b64_audio)} chars', flush=True)

async def client_sim():
    print("Connecting to ws://127.0.0.1:8092/ws ...", flush=True)
    async with websockets.connect('ws://127.0.0.1:8092/ws') as ws:
        print('Client connected to WebSocket!', flush=True)
        # 1. Simulate PTT tap
        await ws.send(json.dumps({"type": "ptt_start"}))
        print('Sent ptt_start', flush=True)
        await asyncio.sleep(0.3)
        
        # 2. Simulate sending voice audio WAV payload
        payload = json.dumps({
            'type': 'voice_audio',
            'format': 'wav',
            'sample_rate': 16000,
            'data': b64_audio
        })
        await ws.send(payload)
        print('Dispatched voice_audio packet! Waiting for Whisper...', flush=True)
        
        # Wait for Whisper transcription
        for i in range(25):
            await asyncio.sleep(0.4)
            if bridge.has_voice_command():
                cmd = bridge.get_voice_command()
                print(f'🎉 TEST SUCCESS! Mobile Bridge confirmed voice destination: [{cmd}]', flush=True)
                return True
        print('❌ Timeout waiting for voice command', flush=True)
        return False

success = asyncio.run(client_sim())
bridge.is_running = False
sys.exit(0 if success else 1)
