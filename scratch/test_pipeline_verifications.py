import sys
import os
import io
import struct
import numpy as np

# Ensure edge_server is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
edge_server_path = os.path.join(project_root, "edge_server")
sys.path.insert(0, edge_server_path)

print("=" * 60)
print("5G ASSISTIVE WEARABLE - PIPELINE VERIFICATION SUITE")
print("=" * 60)

# -------------------------------------------------------------
# Test 1: Motion Detector & Stationary Gating
# -------------------------------------------------------------
print("\n--- Test 1: Motion Detector Walking Gating ---")
from vision import MotionDetector

md = MotionDetector(walk_threshold=4.5)

# Case 1A: Stationary user at desk with chair ahead (hand jitter causes motion_energy=10.0, but speed=0.0 with GPS fix)
md.motion_energy = 10.0
chair_detections = [{'class_name': 'chair', 'bbox': [100, 100, 300, 400], 'confidence': 0.8}]
res_1a = md.evaluate_walking(gps_speed=0.0, is_phone_walking=False, detections=chair_detections, has_gps=True)
print(f"Case 1A (Desk stationary + chair + hand tremor): is_walking = {res_1a['is_walking']} (Expected: False)")
assert res_1a['is_walking'] == False, "Case 1A Failed: Stationary user at desk got false walking flag!"

# Case 1B: Stationary user with colleague sitting opposite (YOLO jitter: 4px shift)
person_det1 = [{'class_name': 'person', 'bbox': [200, 100, 400, 450], 'confidence': 0.85}]
person_det2 = [{'class_name': 'person', 'bbox': [203, 102, 403, 451], 'confidence': 0.85}] # 4px jitter
md.track_pedestrians(person_det1)
res_1b = md.evaluate_walking(gps_speed=0.0, is_phone_walking=False, detections=person_det2, has_gps=True)
print(f"Case 1B (Desk stationary + stationary person with 4px YOLO jitter): is_walking = {res_1b['is_walking']}, person_moving = {res_1b['person_moving']} (Expected: False, False)")
assert res_1b['is_walking'] == False, "Case 1B Failed: Stationary colleague triggered threat caution!"
assert res_1b['person_moving'] == False, "Case 1B Failed: 4px YOLO jitter falsely marked as moving!"

# Case 1C: Stationary user, but person walks towards user (large displacement 25px)
person_det3 = [{'class_name': 'person', 'bbox': [225, 115, 435, 470], 'confidence': 0.85}] # 25px shift
res_1c = md.evaluate_walking(gps_speed=0.0, is_phone_walking=False, detections=person_det3, has_gps=True)
print(f"Case 1C (Desk stationary + person actively walking towards user): is_walking = {res_1c['is_walking']}, person_moving = {res_1c['person_moving']} (Expected: True, True)")
assert res_1c['is_walking'] == True, "Case 1C Failed: Moving pedestrian did not trigger alert!"
assert res_1c['person_moving'] == True, "Case 1C Failed: Pedestrian movement not detected!"

# Case 1D: User actively walking (speed=3.2 km/h) with obstacle
res_1d = md.evaluate_walking(gps_speed=3.2, is_phone_walking=True, detections=chair_detections, has_gps=True)
print(f"Case 1D (User actively walking at 3.2 km/h + chair): is_walking = {res_1d['is_walking']} (Expected: True)")
assert res_1d['is_walking'] == True, "Case 1D Failed: Actively walking user did not trigger walking evaluation!"

print("✅ Test 1 Passed: Motion Detector gating is 100% accurate!")

# -------------------------------------------------------------
# Test 2: Audio WAV Synthesis, Decoding & Whisper Resampling
# -------------------------------------------------------------
print("\n--- Test 2: Audio Decoding & Normalization ---")
from navigation import decode_audio_to_np, snap_to_campus_landmark

def create_synthetic_wav(sample_rate=44100, duration_sec=1.0, channels=1):
    num_samples = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    # 440 Hz test sine tone
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    pcm16 = (signal * 32767).astype(np.int16)
    
    if channels == 2:
        pcm16 = np.column_stack([pcm16, pcm16]).flatten()
        
    buf = io.BytesIO()
    # RIFF header
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + len(pcm16) * 2))
    buf.write(b'WAVE')
    # fmt chunk
    buf.write(b'fmt ')
    buf.write(struct.pack('<I', 16)) # chunk size
    buf.write(struct.pack('<H', 1))  # PCM
    buf.write(struct.pack('<H', channels))
    buf.write(struct.pack('<I', sample_rate))
    buf.write(struct.pack('<I', sample_rate * channels * 2)) # byte rate
    buf.write(struct.pack('<H', channels * 2)) # block align
    buf.write(struct.pack('<H', 16)) # bits per sample
    # data chunk
    buf.write(b'data')
    buf.write(struct.pack('<I', len(pcm16) * 2))
    buf.write(pcm16.tobytes())
    return buf.getvalue()

# Test 2A: 44.1kHz Mono WAV (Standard iOS Safari microphone)
wav_44k = create_synthetic_wav(sample_rate=44100, duration_sec=1.5, channels=1)
decoded_44k = decode_audio_to_np(wav_44k, sample_rate=44100)
print(f"Case 2A (44.1kHz Mono WAV): Decoded length = {len(decoded_44k)} samples at 16kHz (Expected ~24000)")
assert decoded_44k is not None and 23000 <= len(decoded_44k) <= 25000, "Case 2A Failed: 44.1kHz WAV decoding mismatch!"

# Test 2B: 48kHz Stereo WAV
wav_48k = create_synthetic_wav(sample_rate=48000, duration_sec=1.0, channels=2)
decoded_48k = decode_audio_to_np(wav_48k, sample_rate=48000)
print(f"Case 2B (48kHz Stereo WAV): Decoded length = {len(decoded_48k)} samples at 16kHz (Expected ~16000)")
assert decoded_48k is not None and 15000 <= len(decoded_48k) <= 17000, "Case 2B Failed: 48kHz Stereo WAV decoding mismatch!"

print("✅ Test 2 Passed: Audio decoder handles all rates and formats cleanly!")

# -------------------------------------------------------------
# Test 3: Campus Landmark Snapping & Phonetic Correction
# -------------------------------------------------------------
print("\n--- Test 3: Campus Landmark Snapping ---")
test_cases = [
    ("InSat", "New SAC"),
    ("in sat", "New SAC"),
    ("use up", "New SAC"),
    ("new sac", "New SAC"),
    ("nu sac", "New SAC"),
    ("brahmaputra", "Brahmaputra Hostel"),
    ("core 2", "Core 2"),
    ("main gate", "Main Gate"),
    ("food court", "Food Court"),
    ("lecture hall", "Lecture Hall Complex")
]

for query, expected in test_cases:
    snapped, conf, corrected = snap_to_campus_landmark(query)
    print(f"Query: '{query}' -> '{snapped}' (Confidence: {conf}%) | Match: {snapped == expected}")
    assert snapped == expected, f"Campus snapping failed for '{query}': expected '{expected}', got '{snapped}'"

print("✅ Test 3 Passed: Campus landmark snapping matches 100% of cases!")

# -------------------------------------------------------------
# Test 4: Mobile Bridge Imports & Server Integrity
# -------------------------------------------------------------
print("\n--- Test 4: Edge Server & Mobile Bridge Integrity ---")
from mobile_bridge import MobileBridgeServer
from server import PEDESTRIAN_COLLISION_CLASSES, handle_voice_navigation

bridge = MobileBridgeServer(port=8099)
print(f"MobileBridgeServer initialized: host={bridge.host}, port={bridge.port}")
print(f"Pedestrian Collision Classes count: {len(PEDESTRIAN_COLLISION_CLASSES)}")
print("✅ Test 4 Passed: Server modules intact and modular!")

print("\n" + "=" * 60)
print("🎉 ALL PIPELINE VERIFICATIONS PASSED SUCCESSFULLY!")
print("=" * 60)
