import sys, os
sys.path.insert(0, os.getcwd())
from edge_server.navigation.campus_snapping import snap_to_campus_landmark, CAMPUS_LANDMARKS

test_words = [
    "take me to",
    "go to",
    "track",
    "the",
    "to the",
    "to",
    "navigate",
    "navigate to",
    "athletic",
    "athletics",
    "brahma",
    "dhansiri",
    "brahmaputra",
    "dhansiri hostel",
    "brahma hostel",
    "hostel",
    "a",
    "at",
    "act",
    "attic",
    "static",
    "traffic",
    "threat",
    "threat alert",
    "hazard",
    "walking",
    "caution",
    "alert"
]

for w in test_words:
    snapped, conf, corrected = snap_to_campus_landmark(w)
    if "athletic" in snapped.lower() or "ground" in snapped.lower():
        print(f"⚠️ '{w}' SNAPPED TO -> '{snapped}' ({conf}%)")
