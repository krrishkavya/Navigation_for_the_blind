import os
import sys
import time
import json
import numpy as np
import cv2

# Set paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
server_dir = os.path.join(project_root, "edge_server")
sys.path.append(server_dir)

print("=" * 60)
print("     5G ASSISTIVE WEARABLE - MODULAR SYSTEM TEST SUITE     ")
print("=" * 60)

# --- Test 1: Vision Subsystem ---
print("\n[TEST 1] Testing Vision Module (vision/)...")
from vision import MotionDetector, draw_navigation_hud, draw_threat_boxes, draw_qr_overlay

motion = MotionDetector(walk_threshold=1.0)
f1 = np.zeros((480, 640, 3), dtype=np.uint8)
f2 = np.ones((480, 640, 3), dtype=np.uint8) * 50

e1 = motion.update_frame(f1)
e2 = motion.update_frame(f2)
print(f"  ✓ Motion Detector computed frame differencing: e1={e1:.2f}, e2={e2:.2f}")

eval_res = motion.evaluate_walking(gps_speed=1.2, is_phone_walking=False)
assert eval_res["is_walking"] == True
print(f"  ✓ Walking evaluation passed (GPS speed 1.2 km/h -> is_walking={eval_res['is_walking']})")

nav_state_sample = {
    "destination_name": "New SAC",
    "total_distance_m": 420,
    "current_step": "Step 1 of 4: Head north toward Main Road"
}
draw_navigation_hud(f1, (26.1885, 91.6917), 120.0, nav_state_sample, gps_mode="5G SATELLITE", current_speed=1.2)
print("  ✓ Navigation HUD rendering completed with zero errors.")

threats = [{"name": "person", "distance": 1.4, "bbox": (100, 100, 200, 300)}]
draw_threat_boxes(f1, threats, is_walking=True)
print("  ✓ Threat box rendering completed with zero errors.")

# --- Test 2: Navigation & Landmark Registry ---
print("\n[TEST 2] Testing Navigation Module (navigation/)...")
from navigation import snap_to_campus_landmark, IITG_CAMPUS_COORDINATES, geocode_location

test_cases = [
    ("New SAC", "New SAC"),
    ("student activities until", "New SAC"),
    ("Brahmaputra", "Brahmaputra Hostel"),
    ("Central Lib", "Central Library"),
    ("hospital", "Health Centre"),
    ("Khokha", "Khokha Market")
]

for query, expected in test_cases:
    snapped, conf, corrected = snap_to_campus_landmark(query)
    assert snapped == expected, f"Expected {expected}, got {snapped}"
    print(f"  ✓ Snapped '{query}' -> '{snapped}' (Conf: {conf}%)")

pin = geocode_location("Brahmaputra")
assert pin is not None
print(f"  ✓ Resolved coordinates for Brahmaputra: {pin}")

# --- Test 3: Audio Decoding Helper ---
print("\n[TEST 3] Testing Audio Decoding Pipeline...")
from navigation import decode_audio_to_np
import io, wave

# Generate clean synthetic 16kHz WAV byte stream
buf = io.BytesIO()
with wave.open(buf, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    samples = (np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, 8000)) * 16000).astype(np.int16)
    wf.writeframes(samples.tobytes())
wav_bytes = buf.getvalue()

decoded_np = decode_audio_to_np(wav_bytes, sample_rate=16000)
assert decoded_np is not None
assert len(decoded_np) == 8000
print(f"  ✓ Audio decoder processed synthetic WAV: {len(decoded_np)} samples at 16kHz float32.")

# --- Test 4: Web Client Files & HTTP Gateway ---
print("\n[TEST 4] Testing Web Client Asset Loading (web_client/)...")
from mobile_bridge import INDEX_HTML_PATH, STYLE_CSS_PATH, APP_JS_PATH, MAP_HTML_PATH

assert os.path.exists(INDEX_HTML_PATH), f"Missing {INDEX_HTML_PATH}"
assert os.path.exists(STYLE_CSS_PATH), f"Missing {STYLE_CSS_PATH}"
assert os.path.exists(APP_JS_PATH), f"Missing {APP_JS_PATH}"
assert os.path.exists(MAP_HTML_PATH), f"Missing {MAP_HTML_PATH}"

print(f"  ✓ index.html size : {os.path.getsize(INDEX_HTML_PATH)} bytes")
print(f"  ✓ style.css size  : {os.path.getsize(STYLE_CSS_PATH)} bytes")
print(f"  ✓ app.js size     : {os.path.getsize(APP_JS_PATH)} bytes")
print(f"  ✓ live_map.html   : {os.path.getsize(MAP_HTML_PATH)} bytes")

# --- Test 5: Server Orchestrator Imports ---
print("\n[TEST 5] Validating Server Orchestrator (server.py & server_main.py)...")
import server
import server_main
print("  ✓ Both server.py and server_main.py imported and validated successfully!")

print("\n" + "=" * 60)
print("     ALL TESTS PASSED! NEW SIMPLIFIED NAMES VERIFIED! ")
print("=" * 60)
