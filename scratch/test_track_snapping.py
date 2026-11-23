import sys, os
sys.path.insert(0, os.getcwd())
from edge_server.navigation.campus_snapping import snap_to_campus_landmark

phrases = ["track", "the track", "at the track", "a track", "back", "pack", "that"]
for p in phrases:
    s, c, was = snap_to_campus_landmark(p)
    print(f"'{p}' -> '{s}' ({c}%, corrected={was})")
