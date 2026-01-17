import time
import subprocess
import mysql.connector
from datetime import datetime, timezone

# DB CONFIG
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "5568",
    "database": "jalrakshak"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def setup_test_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    node_id = "TEST_NODE_ALERT_999"
    
    # Clean up
    cursor.execute("DELETE FROM alerts WHERE node_id = %s", (node_id,))
    cursor.execute("DELETE FROM sensor_readings WHERE node_id = %s", (node_id,))
    cursor.execute("DELETE FROM node_status WHERE node_id = %s", (node_id,))
    cursor.execute("DELETE FROM nodes WHERE node_id = %s", (node_id,))
    
    # Insert Node
    print(f"Creating test node: {node_id}")
    cursor.execute("""
        INSERT INTO nodes (node_id, hierarchy_level, pump, installed_on)
        VALUES (%s, %s, %s, %s)
    """, (node_id, 1, "Test Pump", datetime.now().date()))
    
    conn.commit()
    return node_id, conn

def insert_reading_bad(node_id, conn):
    cursor = conn.cursor()
    # Bad reading (coliform > 0 -> RED immediately, or bad values)
    # Let's use High Turbidity for AMBER/RED?
    # CWQI < 50 is RED.
    # Turbidity > 5 is 0 score.
    # If all bad, score is low.
    
    # Let's insert Coliform = 100 (Score 0) -> High weight 0.25 -> 0.
    # Actually Coliform=0 is 100 score. Coliform > 10 is 0 score.
    # Let's make it very bad.
    
    print(f"Inserting BAD reading for {node_id}")
    cursor.execute("""
        INSERT INTO sensor_readings (
            node_id, turbidity, ph, fluoride, coliform,
            conductivity, temperature, dissolved_oxygen, pressure
        ) VALUES (%s, 10.0, 4.0, 2.0, 100, 2000, 40, 1.0, 0.5)
    """, (node_id,))
    conn.commit()

def insert_reading_good(node_id, conn):
    cursor = conn.cursor()
    print(f"Inserting GOOD reading for {node_id}")
    cursor.execute("""
        INSERT INTO sensor_readings (
            node_id, turbidity, ph, fluoride, coliform,
            conductivity, temperature, dissolved_oxygen, pressure
        ) VALUES (%s, 0.5, 7.0, 0.5, 0, 300, 25, 7.0, 3.0)
    """, (node_id,))
    conn.commit()

def check_alerts(node_id, conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM alerts WHERE node_id = %s ORDER BY alert_id DESC", (node_id,))
    alerts = cursor.fetchall()
    for a in alerts:
        print(f"ALERT FOUND: ID={a['alert_id']}, Level={a['alert_level']}, Status={a['is_active']}, Reason={a['reason']}")
    return alerts

def run_analyzer_step():
    # Run analyzer for a few seconds
    print("Running CWQI Analyzer...")
    proc = subprocess.Popen(["python", "cwqi_analyzer.py"])
    time.sleep(8) # Wait for startup + processing (interval is 5s)
    print("Stopping CWQI Analyzer...")
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()

def main():
    node_id, conn = setup_test_data()
    
    try:
        # 1. Trigger Alert
        insert_reading_bad(node_id, conn)
        run_analyzer_step()
        
        alerts = check_alerts(node_id, conn)
        active = [a for a in alerts if a['is_active']]
        if active:
            print("SUCCESS: Alert raised.")
        else:
            print("FAILURE: No active alert found.")
            
        # 2. Resolve Alert
        insert_reading_good(node_id, conn)
        run_analyzer_step()
        
        alerts = check_alerts(node_id, conn)
        active = [a for a in alerts if a['is_active']]
        if not active:
            print("SUCCESS: Alerts resolved.")
        else:
            print("FAILURE: Alerts still active.")
            
    finally:
        # Cleanup
        # setup_test_data() # Option to clean up at end
        conn.close()

if __name__ == "__main__":
    main()
