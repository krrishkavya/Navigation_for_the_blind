"""
Targeted Verification for Voice Decoding, Landmark Snapping & Walking Threat Gating
"""
import os
import sys
import numpy as np

# Ensure root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from edge_server.navigation.speech_to_text import decode_audio_to_np, transcribe_audio_np
from edge_server.navigation.campus_snapping import snap_to_campus_landmark
from edge_server.vision.motion_detector import MotionDetector

def test_voice_decoding_and_snapping():
    print("\n--- [VERIFICATION 1] Testing Voice Decoding & Landmark Snapping ---")
    wav_path = os.path.join(ROOT_DIR, "captured_voice_debug.wav")
    assert os.path.exists(wav_path), "captured_voice_debug.wav must exist"
    
    with open(wav_path, "rb") as f:
        raw_bytes = f.read()
        
    audio_np = decode_audio_to_np(raw_bytes)
    assert audio_np is not None and len(audio_np) > 0, "Decoded audio cannot be empty"
    print(f"✓ Decoded audio shape: {audio_np.shape}, dtype: {audio_np.dtype}")
    
    dest = transcribe_audio_np(audio_np)
    print(f"✓ Transcribed Destination: '{dest}'")
    assert dest == "New SAC", f"Expected 'New SAC', got '{dest}'"
    print("  --> Passed: User's recorded audio resolves to 'New SAC' with 100% precision!\n")

def test_walking_threat_gating():
    print("--- [VERIFICATION 2] Testing Walking Threat Gating ---")
    md = MotionDetector(walk_threshold=4.5)
    
    # Mock frame 1 & 2 for optical flow
    f1 = np.zeros((240, 320, 3), dtype=np.uint8)
    f2 = np.zeros((240, 320, 3), dtype=np.uint8)
    f2[100:150, 100:150] = 50 # slight noise
    
    md.update_frame(f1)
    md.update_frame(f2)
    
    # Case A: Stationary user, stationary person ahead (desk/test scenario from screenshot!)
    # In screenshot: Motion: 0.7, PersonMoving: False, Speed: 0.0 km/h
    detections_stationary_person = [
        {'class_name': 'person', 'bbox': [100, 50, 200, 220], 'confidence': 0.85}
    ]
    # Update once to populate previous centers
    md.track_pedestrians(detections_stationary_person)
    
    # Evaluate walking when neither person nor user is moving
    eval_stationary = md.evaluate_walking(gps_speed=0.0, is_phone_walking=False, detections=detections_stationary_person)
    print("Case A (Stationary User + Stationary Person):", eval_stationary)
    assert not eval_stationary["is_walking"], "Must NOT be walking when user and person are both stationary!"
    print("  --> Passed: No false threat cautions when standing/sitting stationary!\n")
    
    # Case B: Stationary user, but person in front is WALKING / approaching
    detections_walking_person = [
        {'class_name': 'person', 'bbox': [110, 40, 225, 235], 'confidence': 0.88} # moved by > 10 pixels
    ]
    eval_person_walking = md.evaluate_walking(gps_speed=0.0, is_phone_walking=False, detections=detections_walking_person)
    print("Case B (Stationary User + Person Moving Ahead):", eval_person_walking)
    assert eval_person_walking["is_walking"], "Must be walking when person in front is moving towards/across!"
    print("  --> Passed: Caution enabled when person in front is actively moving!\n")
    
    # Case C: User is walking (GPS speed 1.4 km/h), obstacle ahead
    eval_user_walking = md.evaluate_walking(gps_speed=1.4, is_phone_walking=True, detections=detections_stationary_person)
    print("Case C (User Walking + Obstacle Ahead):", eval_user_walking)
    assert eval_user_walking["is_walking"], "Must be walking when user GPS speed >= 1.0 km/h!"
    print("  --> Passed: Caution enabled when user is walking!\n")

if __name__ == "__main__":
    test_voice_decoding_and_snapping()
    test_walking_threat_gating()
    print("============================================================")
    print("     ALL TARGETED VERIFICATIONS PASSED SUCCESSFULLY!        ")
    print("============================================================")
