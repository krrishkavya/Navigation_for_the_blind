import sys
import os
import json

sys.path.append(r'2_Edge_Server_AI\navigation_module')
from osrm_routing import IITG_CAMPUS_COORDINATES
from campus_snapping import CAMPUS_LANDMARKS

unified = []

for item in CAMPUS_LANDMARKS:
    canonical = item["canonical"]
    aliases = list(item.get("aliases", []))
    
    # Add nanotechnology alias if Centre for Nanotechnology
    if canonical == "Centre for Nanotechnology" and "nanotechnology" not in aliases:
        aliases.append("nanotechnology")
        
    coords = None
    for name in [canonical.lower()] + [a.lower() for a in aliases]:
        if name in IITG_CAMPUS_COORDINATES:
            coords = list(IITG_CAMPUS_COORDINATES[name])
            break
            
    unified.append({
        "canonical": canonical,
        "coordinates": coords,
        "aliases": aliases
    })

out_path = r'2_Edge_Server_AI\navigation_module\campus_landmarks.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(unified, f, indent=2)

print(f"Updated {out_path} with all coordinates and aliases.")
