import cv2
import numpy as np
import time
import os
import sys

current_dir = os.path.abspath('2_Edge_Server_AI')
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'vision_module'))
sys.path.append(os.path.join(current_dir, 'navigation_module'))

from mobile_5g_bridge import MobileBridgeServer
from udp_network_handler import UDPNetworkHandler

# Test 1: Stale frame handling
bridge = MobileBridgeServer(host="127.0.0.1", port=9999)
dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
bridge.latest_frame = dummy_img
bridge.latest_frame_time = time.time() - 5.0 # 5s old frame
f, t = bridge.get_latest_frame()
assert f is None, "Stale frame was not discarded!"
print("Test 1 PASS: Stale frame properly discarded after timeout.")

# Test 2: Fresh frame handling
bridge.latest_frame = dummy_img
bridge.latest_frame_time = time.time()
f, t = bridge.get_latest_frame()
assert f is not None, "Fresh frame was not returned!"
print("Test 2 PASS: Fresh frame properly returned.")

print("All pipeline assertions verified successfully!")
