import sys, os
sys.path.insert(0, os.getcwd())
from edge_server.navigation.speech_to_text import clean_destination_query
from edge_server.navigation.campus_snapping import snap_to_campus_landmark

test_inputs = [
    'navigate me to Brahmaputra',
    'navigate me to Dhansiri',
    'navigate me to New SAC',
    'navigate me to Central Library',
    'Brahmaputra',
    'Dhansiri',
    'New SAC',
    'take me to Brahmaputra',
    'go to Dhansiri'
]

print("Verifying 'navigate me' prefix cleaning and landmark resolution:")
for t in test_inputs:
    cleaned = clean_destination_query(t)
    snapped, conf, corrected = snap_to_campus_landmark(cleaned or t)
    print(f"  '{t}' -> Cleaned: '{cleaned}' -> Snapped: '{snapped}' ({conf}%)")
    assert snapped in ['Brahmaputra Hostel', 'Dhansiri Hostel', 'New SAC', 'Central Library']

print("All tests passed 100%!")
