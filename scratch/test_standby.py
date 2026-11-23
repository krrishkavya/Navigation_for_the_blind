import sys, os
sys.path.append(os.path.abspath('2_Edge_Server_AI'))
from tunnel_manager import CloudflareTunnelManager

tm = CloudflareTunnelManager(port=8080, auto_start=False)
frame = tm.render_standby_frame((480, 640))
assert frame is not None and frame.shape == (480, 640, 3)
print("Standby frame rendered successfully with shape:", frame.shape)
