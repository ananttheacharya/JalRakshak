import mysql.connector
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import re

# MySQL CONFIG
DB_CONFIG = {
    "host": "localhost",
    "user": "jalrakshak",
    "password": "jalrakshak123",
    "database": "jalrakshak"
}

# Fallback coordinates
JAIPUR_PHED_COORDS = (26.8997, 75.8048)
JHOTWARA_COORDS = (26.9392, 75.7562)
VIDHYADHAR_NAGAR_COORDS = (26.9654, 75.7766)
MACHEDA_COORDS = (27.0003, 75.7483)

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def clean_name(name):
    if not name:
        return ""
    # Remove noise
    name = re.sub(r'\(N\)', '', name, flags=re.I)
    name = re.sub(r'\(SOUTH\)', ' South', name, flags=re.I)
    name = re.sub(r'\(S\)', ' South', name, flags=re.I)
    name = re.sub(r'UWSS', '', name, flags=re.I)
    name = re.sub(r'CSD', 'Sub Division', name, flags=re.I)
    name = re.sub(r'_', ' ', name)
    return name.strip()

def populate_coordinates():
    geolocator = Nominatim(user_agent="jalrakshak_geocoder_v3")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all nodes to build a cache of parent coords
    cursor.execute("SELECT node_id, hierarchy_level, pump, zone, colony, latitude, longitude FROM nodes")
    all_nodes = cursor.fetchall()
    
    # Cache for hierarchical fallbacks
    coords_cache = {}
    for n in all_nodes:
        if n['latitude'] and n['longitude']:
            coords_cache[n['node_id']] = (float(n['latitude']), float(n['longitude']))

    # Nodes to process (limit to avoid hitting rate limits too hard in one go, but enough for a good batch)
    nodes_to_process = [n for n in all_nodes if n['latitude'] is None or n['longitude'] is None]

    if not nodes_to_process:
        print("All nodes already have coordinates.")
        return

    print(f"Found {len(nodes_to_process)} nodes to geocode.")

    for node in nodes_to_process:
        node_id = node['node_id']
        level = node['hierarchy_level']
        
        # Check for abnormal names
        abnormal_keywords = ["DIRECT_SUPPLY", "UWSS", "GLOBAL", "C/O", "G.L."]
        if any(keyword in node_id.upper() for keyword in abnormal_keywords):
            print(f"Abnormal node name {node_id}, using PHED fallback.")
            location_coords = JAIPUR_PHED_COORDS
        else:
            # Construct address hierarchy
            parts = []
            if node['colony']: parts.append(clean_name(node['colony']))
            if node['zone']: parts.append(clean_name(node['zone']))
            if node['pump']: parts.append(clean_name(node['pump']))
            
            address = ", ".join(parts) + ", Jaipur, Rajasthan, India"
            print(f"Geocoding {node_id}: {address}")

            location = None
            retries = 2
            while retries > 0:
                try:
                    location = geolocator.geocode(address, timeout=10)
                    break
                except GeocoderTimedOut:
                    retries -= 1
                    time.sleep(1)
            
            if location:
                location_coords = (location.latitude, location.longitude)
                print(f"Found: {location_coords}")
            else:
                # Fallback to Parent logic
                parent_key = None
                if level == 2:
                    parent_key = f"L1_{node['pump'].replace(' ', '_').upper()}"
                elif level == 3:
                    # Try to find L2 parent: Zone + Pump
                    zp = f"{node['pump']}_{node['zone']}".replace(' ', '_').upper()
                    parent_key = f"L2_{zp}"
                
                if parent_key and parent_key in coords_cache:
                    location_coords = coords_cache[parent_key]
                    print(f"Fallback to parent {parent_key}: {location_coords}")
                else:
                    # Final fallback: Check specific areas or Pump only
                    nupp = node_id.upper()
                    if "JHOTWARA" in nupp:
                         location_coords = JHOTWARA_COORDS
                         print(f"Fallback to JHOTWARA: {location_coords}")
                    elif "VID" in nupp or "VIDHYADHAR" in nupp:
                         location_coords = VIDHYADHAR_NAGAR_COORDS
                         print(f"Fallback to VIDHYADHAR NAGAR: {location_coords}")
                    elif "MACHEDA" in nupp:
                         location_coords = MACHEDA_COORDS
                         print(f"Fallback to MACHEDA: {location_coords}")
                    else:
                        pump_name = clean_name(node['pump'])
                        pump_address = f"{pump_name}, Jaipur, Rajasthan, India"
                        print(f"Fallback to pump address: {pump_address}")
                        try:
                            location = geolocator.geocode(pump_address, timeout=10)
                            if location:
                                location_coords = (location.latitude, location.longitude)
                                print(f"Found (pump): {location_coords}")
                            else:
                                location_coords = JAIPUR_PHED_COORDS
                                print(f"No result found, using Jaipur PHED fallback.")
                        except:
                            location_coords = JAIPUR_PHED_COORDS

        # Update Database
        try:
            cursor.execute(
                "UPDATE nodes SET latitude = %s, longitude = %s WHERE node_id = %s",
                (location_coords[0], location_coords[1], node_id)
            )
            conn.commit()
            # Update local cache
            coords_cache[node_id] = location_coords
        except Exception as e:
            print(f"Database update error for {node_id}: {e}")

        # Respect Nominatim usage policy (1 request per second)
        time.sleep(1.1)

    cursor.close()
    conn.close()
    print("Geocoding complete.")

if __name__ == "__main__":
    populate_coordinates()
