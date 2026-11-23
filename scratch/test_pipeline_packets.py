import cv2
import numpy as np
import time
import os
import sys

# Test the exact detection and depth pipeline from server_main.py
current_dir = os.path.abspath('2_Edge_Server_AI')
sys.path.append(os.path.join(current_dir, 'vision_module'))

from yolo_detector import YoloDetector
from depth_estimator import DepthEstimator

detector = YoloDetector('yolov8m.pt')
depth_model = DepthEstimator()

# Use bus.jpg as test packet 1
bus_path = r".venv\Lib\site-packages\ultralytics\assets\bus.jpg"
frame1 = cv2.imread(bus_path)
print("Loaded test frame 1:", frame1.shape)

# Create a second frame slightly shifted to simulate a walking person
h, w = frame1.shape[:2]
M = np.float32([[1, 0, 5], [0, 1, 0]]) # shift 5px horizontally
frame2 = cv2.warpAffine(frame1, M, (w, h))

PEDESTRIAN_COLLISION_CLASSES = {
    'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck',
    'traffic light', 'fire hydrant', 'stop sign', 'bench',
    'chair', 'couch', 'potted plant', 'table', 'dining table',
    'dog', 'horse', 'cow', 'suitcase', 'backpack', 'umbrella',
    'trash can', 'pole', 'stairs', 'barrier', 'door'
}

CALIBRATION_CONSTANT = 1100.0
COLLISION_ALERT_DISTANCE_M = 3.5
CRITICAL_STOP_DISTANCE_M = 1.5

def evaluate_frame(frame, prev_centers, prev_gray):
    h, w = frame.shape[:2]
    # Motion energy
    gray_small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (120, 90))
    gray_blur = cv2.GaussianBlur(gray_small, (15, 15), 0)
    frame_diff = float(np.mean(cv2.absdiff(prev_gray, gray_blur))) if prev_gray is not None else 0.0
    
    # YOLO
    dets = detector.detect_objects(frame, confidence_threshold=0.35)
    # Depth
    depth_res = depth_model.estimate_depth(frame)
    raw_depth = depth_res[0] if isinstance(depth_res, (tuple, list)) else depth_res
    if hasattr(raw_depth, 'cpu'):
        raw_depth = raw_depth.cpu().numpy()
    if hasattr(raw_depth, 'ndim') and raw_depth.ndim == 3:
        raw_depth = raw_depth.squeeze()
        
    current_person_centers = []
    person_moving = False
    valid_threats = []
    
    walking_corridor_xmin = int(w * 0.20)
    walking_corridor_xmax = int(w * 0.80)
    
    for det in dets:
        x1, y1, x2, y2 = det['bbox']
        cname = det['class_name'].lower().strip()
        conf = det['confidence']
        bx1, by1, bx2, by2 = int(x1), int(y1), int(x2), int(y2)
        cx, cy = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
        
        if cname == 'person':
            current_person_centers.append((cx, cy, bx2 - bx1, by2 - by1))
            # Check displacement against previous person centers
            for pcx, pcy, pw, ph in prev_centers:
                dist_moved = np.hypot(cx - pcx, cy - pcy)
                size_diff = abs((bx2 - bx1) - pw)
                if dist_moved >= 3.0 or size_diff >= 3.0:
                    person_moving = True
                    break
        
        if cname not in PEDESTRIAN_COLLISION_CLASSES:
            continue
            
        in_path = (bx1 <= walking_corridor_xmax and bx2 >= walking_corridor_xmin)
        if in_path:
            crop = raw_depth[by1:by2, bx1:bx2]
            if crop.size > 0:
                med = float(np.median(crop))
                if med > 1.0:
                    dist_m = float(CALIBRATION_CONSTANT / med)
                    valid_threats.append({'name': cname, 'distance': dist_m, 'bbox': (bx1, by1, bx2, by2)})
                    
    valid_threats.sort(key=lambda x: x['distance'])
    camera_walking = (frame_diff >= 1.0)
    is_walking = camera_walking or person_moving
    
    return is_walking, person_moving, camera_walking, frame_diff, valid_threats, current_person_centers, gray_blur

# Run on frame 1
is_walk1, p_mov1, c_mov1, diff1, threats1, centers1, gray1 = evaluate_frame(frame1, [], None)
print(f"Frame 1: threats count: {len(threats1)}, walking: {is_walk1}")
for t in threats1:
    print(f"  Threat: {t['name']} at {t['distance']:.2f}m")

# Run on frame 2 (simulating person walked 5px)
is_walk2, p_mov2, c_mov2, diff2, threats2, centers2, gray2 = evaluate_frame(frame2, centers1, gray1)
print(f"Frame 2 (with person motion): person_moving={p_mov2}, camera_walking={c_mov2}, is_walking={is_walk2}")
for t in threats2:
    print(f"  Threat: {t['name']} at {t['distance']:.2f}m")
