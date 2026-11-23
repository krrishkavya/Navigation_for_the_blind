import sys, os
sys.path.insert(0, os.getcwd())
from edge_server.navigation.campus_snapping import snap_to_campus_landmark
from edge_server.navigation.speech_to_text import clean_destination_query

queries = [
    'brahma',
    'dhansiri',
    'brahmaputra',
    'take me to brahma',
    'go to dhansiri',
    'athletic track',
    'brahma hostel',
    'take me to brahmaputra',
    'navigate to dhansiri',
    'navigate to brahma'
]

for q in queries:
    cleaned = clean_destination_query(q)
    snapped, conf, corrected = snap_to_campus_landmark(cleaned or q)
    print(f'Input: "{q}" -> Cleaned: "{cleaned}" -> Snapped: "{snapped}" ({conf}%, corrected={corrected})')
