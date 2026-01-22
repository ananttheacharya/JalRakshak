import random
import time
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from collections import defaultdict

# -------- MySQL CONFIG --------
DB_CONFIG = {
    "host": "localhost",
    "user": "jalrakshak",
    "password": "jalrakshak123",
    "database": "jalrakshak"
}

# -------- GLOBALS --------
HIERARCHY_MAP = defaultdict(list)  # parent_id -> [child_ids]
NODE_DETAILS = {}  # node_id -> {level, pump, zone}
CONTAMINATION_QUEUE = []  # List of {node_id, trigger_time, severity}

# -------- CONNECT --------
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# -------- BUILD HIERARCHY --------
def build_hierarchy_map():
    global HIERARCHY_MAP, NODE_DETAILS
    print("[SIMULATOR] Building Hierarchy Map...")
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT node_id, hierarchy_level, pump, zone, colony FROM nodes")
        nodes = cursor.fetchall()
        
        # 1. Index all nodes
        l1_nodes = {}
        l2_nodes = {}
        
        for n in nodes:
            NODE_DETAILS[n['node_id']] = n
            if n['hierarchy_level'] == 1:
                l1_nodes[n['pump']] = n['node_id']
            elif n['hierarchy_level'] == 2:
                key = f"{n['pump']}_{n['zone']}"
                l2_nodes[key] = n['node_id']

        # 2. Map Parents to Children
        for n in nodes:
            if n['hierarchy_level'] == 2:
                parent_id = l1_nodes.get(n['pump'])
                if parent_id:
                    HIERARCHY_MAP[parent_id].append(n['node_id'])
            
            elif n['hierarchy_level'] == 3:
                parent_key = f"{n['pump']}_{n['zone']}"
                parent_id = l2_nodes.get(parent_key)
                if parent_id:
                    HIERARCHY_MAP[parent_id].append(n['node_id'])
        
        print(f"[SIMULATOR] Mapped {len(HIERARCHY_MAP)} parent-child relationships.")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"[ERROR] Failed to build hierarchy: {e}")

# -------- SENSOR GENERATORS --------
def generate_reading(node_id, level, current_contamination=None):
    """
    Generates a reading. If current_contamination is set, 
    values will reflect that severity (AMBER/RED).
    """
    
    # Base values
    base = {
        "turbidity": round(random.uniform(0.3, 2.5), 2),
        "ph": round(random.uniform(6.8, 7.6), 2),
        "fluoride": round(random.uniform(0.4, 1.0), 2),
        "coliform": 0,
        "conductivity": round(random.uniform(400, 900), 1),
        "dissolved_oxygen": round(random.uniform(4.5, 7.5), 1)
    }

    if current_contamination:
        severity = current_contamination['severity'] # 'AMBER' or 'RED'
        
        if severity == 'AMBER':
            # Slight drift
            base["turbidity"] = round(random.uniform(4.5, 6.0), 2)
            base["coliform"] = random.randint(10, 50)
        elif severity == 'RED':
            # Major contamination
            base["turbidity"] = round(random.uniform(10.0, 25.0), 2)
            base["coliform"] = random.randint(100, 500)
            base["ph"] = round(random.uniform(5.5, 6.0), 2)

    return {
        "turbidity": base["turbidity"],
        "ph": base["ph"],
        "fluoride": base["fluoride"],
        "coliform": base["coliform"],
        "conductivity": base["conductivity"],
        "temperature": round(random.uniform(24, 32), 1),
        "dissolved_oxygen": base["dissolved_oxygen"],
        "pressure": round(random.uniform(1.5, 3.5), 2),
        "flow_rate": round(random.uniform(8, 25), 1)
    }

# -------- PROPAGATION LOGIC --------
def process_propagation(now):
    """
    Checks the queue for active contaminations.
    Returns a dict: node_id -> {severity}
    """
    active_pollution = {}
    new_queue = []

    for item in CONTAMINATION_QUEUE:
        if now >= item['trigger_time']:
            active_pollution[item['node_id']] = item
            
            # If this is a fresh trigger (within last 5s), schedule children
            # We use a flag 'propagated' to avoid rescheduling endlessly
            if not item.get('propagated'):
                item['propagated'] = True
                children = HIERARCHY_MAP.get(item['node_id'], [])
                for child_id in children:
                    # Delay: 20 seconds for water to flow
                    delay = timedelta(seconds=20) 
                    CONTAMINATION_QUEUE.append({
                        'node_id': child_id,
                        'trigger_time': now + delay,
                        'severity': item['severity'], # Inherit severity
                        'propagated': False
                    })
                    print(f"[PROPAGATION] Scheduled {item['severity']} for {child_id} in 20s")
            
            # Keep active for ~2 mins then clear
            if now < item['trigger_time'] + timedelta(minutes=2):
                 new_queue.append(item)
        else:
            new_queue.append(item) # future event
            
    CONTAMINATION_QUEUE[:] = new_queue
    return active_pollution

# -------- MAIN LOOP --------
def run_simulator():
    build_hierarchy_map()
    
    INSERT_SENSOR_QUERY = """
    INSERT INTO sensor_readings (
        node_id, timestamp, turbidity, ph, fluoride, coliform, 
        conductivity, temperature, dissolved_oxygen, pressure, flow_rate
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("[SIMULATOR] Running... Press Ctrl+C to stop.")
        
        while True:
            now = datetime.now()
            
            # 1. Random Spontaneous Trigger (L1 only)
            # 1% chance every cycle to pollute a random L1 node
            if random.random() < 0.01:
                l1_ids = [n for n, d in NODE_DETAILS.items() if d['hierarchy_level'] == 1]
                if l1_ids:
                    target = random.choice(l1_ids)
                    severity = random.choice(['AMBER', 'RED'])
                    print(f"\n[TRIGGER] Spontaneous {severity} at {target}!")
                    CONTAMINATION_QUEUE.append({
                        'node_id': target,
                        'trigger_time': now, # Immediate
                        'severity': severity,
                        'propagated': False
                    })

            # 2. Process Propagation
            active_pollution = process_propagation(now)
            
            # 3. Generate Readings
            batch = []
            node_ids = list(NODE_DETAILS.keys())
            
            for node_id in node_ids:
                level = NODE_DETAILS[node_id]['hierarchy_level']
                contamination = active_pollution.get(node_id)
                
                # Check normal anomaly chance ONLY if not already receiving simulated pollution
                if not contamination and random.random() < 0.005: 
                    # Tiny chance of random glitch unrelated to flow
                    reading = generate_reading(node_id, level)
                    # corrupt it manually
                    reading['turbidity'] = 15.0 
                else:
                    reading = generate_reading(node_id, level, contamination)
                
                batch.append((
                    node_id, now,
                    reading["turbidity"], reading["ph"], reading["fluoride"],
                    reading["coliform"], reading["conductivity"], reading["temperature"],
                    reading["dissolved_oxygen"], reading["pressure"], reading["flow_rate"]
                ))
            
            cursor.executemany(INSERT_SENSOR_QUERY, batch)
            conn.commit()
            print(f"[SIMULATOR] Batch: {len(batch)} readings | Polluted Nodes: {len(active_pollution)}")
            
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[SIMULATOR] Stopped.")
    except Error as e:
        print(f"[ERROR] {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    run_simulator()
