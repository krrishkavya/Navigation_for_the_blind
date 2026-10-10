import requests

def geocode_location(location_name):
    """
    Converts a text destination (e.g., "Library") into GPS coordinates.
    Uses the free Nominatim (OpenStreetMap) API.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': location_name,
        'format': 'json',
        'limit': 1
    }
    # Nominatim requires a User-Agent header to prevent abuse
    headers = {
        'User-Agent': '5G_Wearable_Navigation_Project_Dev/1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data:
            # Returns (Latitude, Longitude) as floats
            return float(data[0]['lat']), float(data[0]['lon'])
        else:
            return None
    except Exception as e:
        print(f"Error during geocoding: {e}")
        return None

def get_walking_route(start_coords, end_coords):
    """
    Fetches walking directions from OSRM.
    IMPORTANT: OSRM expects coordinates in Longitude,Latitude order!
    """
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    
    # OSRM Endpoint (profile: foot)
    url = f"http://router.project-osrm.org/route/v1/foot/{start_lon},{start_lat};{end_lon},{end_lat}"
    
    params = {
        'steps': 'true',     # We need turn-by-turn steps
        'overview': 'false'  # We don't need the path geometry for audio
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['code'] != 'Ok':
            return []

        # Extract the steps from the JSON response
        steps = data['routes'][0]['legs'][0]['steps']
        
        instructions = []
        for step in steps:
            # OSRM provides a human-readable maneuver type and street name
            maneuver = step['maneuver']['type']
            modifier = step['maneuver'].get('modifier', '')
            street_name = step.get('name', 'the road')
            distance = step['distance'] # in meters
            
            # Skip 0 meter steps
            if distance == 0 and maneuver != 'arrive':
                continue
                
            # Create a simple, human-readable sentence for the TTS engine
            if maneuver == 'depart':
                instruction = f"Head out on {street_name}."
            elif maneuver == 'arrive':
                instruction = "You have arrived at your destination."
            elif modifier:
                instruction = f"Turn {modifier.replace('-', ' ')} onto {street_name}, and walk for {int(distance)} meters."
            else:
                instruction = f"Continue on {street_name} for {int(distance)} meters."
            
            instructions.append(instruction)
            
        return instructions

    except Exception as e:
        print(f"Error fetching route from OSRM: {e}")
        return []

def get_navigation_instructions(start_coords, destination_name):
    """
    Master function: Takes a starting GPS coordinate and a spoken destination,
    returns a list of spoken steps ready for the Text-to-Speech module.
    """
    print(f"Finding coordinates for: '{destination_name}'...")
    end_coords = geocode_location(destination_name)
    
    if not end_coords:
        return ["Sorry, I could not find that location."]
        
    print(f"Destination found at: {end_coords}. Fetching walking route...")
    
    # --- DEBUG FEATURE: VISUAL MAP LINK ---
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    map_url = f"https://www.google.com/maps/dir/?api=1&origin={start_lat},{start_lon}&destination={end_lat},{end_lon}&travelmode=walking"
    print(f"\n🌍 View this route on a visual map here:\n{map_url}\n")
    # --------------------------------------
    
    instructions = get_walking_route(start_coords, end_coords)
    
    if not instructions:
        return ["Sorry, I could not calculate a walking route to that location."]
        
    return instructions

if __name__ == "__main__":
    # --- LOCAL TESTING BLOCK ---
    # Since we don't have the Arduino GPS yet, we hardcode a start location
    # Example: The Empire State Building, NYC
    fake_start_gps = (40.748817, -73.985428) 
    
    # Fake spoken destination (what Speech-to-Text would output)
    spoken_destination = "Times Square, New York"
    
    # Run the pipeline
    steps = get_navigation_instructions(fake_start_gps, spoken_destination)
    
    print("\n--- Route Instructions for Text-To-Speech ---")
    for i, step in enumerate(steps):
        print(f"Step {i+1}: {step}")
