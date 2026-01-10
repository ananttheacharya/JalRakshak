import random
import time
from datetime import datetime
import mysql.connector
from mysql.connector import Error


# -------- MySQL CONFIG --------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "5568",
    "database": "jalrakshak"
}


# -------- CONNECT --------
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# -------- FETCH ALL NODE IDS --------
FETCH_NODES_QUERY = "SELECT node_id, hierarchy_level FROM nodes"


# -------- INSERT SENSOR DATA --------
INSERT_SENSOR_QUERY = """
INSERT INTO sensor_readings (
    node_id,
    timestamp,
    turbidity,
    ph,
    fluoride,
    coliform,
    conductivity,
    temperature,
    dissolved_oxygen,
    pressure,
    flow_rate
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""


# -------- SENSOR GENERATORS --------

def generate_normal_reading(level):
    """Normal baseline values (vary by hierarchy)."""

    pressure_base = {1: 3.5, 2: 2.5, 3: 1.8}.get(level, 2.0)

    return {
        "turbidity": round(random.uniform(0.3, 2.5), 2),
        "ph": round(random.uniform(6.8, 7.6), 2),
        "fluoride": round(random.uniform(0.4, 1.0), 2),
        "coliform": 0,
        "conductivity": round(random.uniform(400, 900), 1),
        "temperature": round(random.uniform(24, 32), 1),
        "dissolved_oxygen": round(random.uniform(4.5, 7.5), 1),
        "pressure": round(random.uniform(pressure_base - 0.5, pressure_base + 0.5), 2),
        "flow_rate": round(random.uniform(8, 25), 1)
    }


def inject_anomaly(reading):
    """Occasionally break one parameter."""
    anomaly_type = random.choice([
        "turbidity", "ph", "fluoride",
        "coliform", "pressure", "do"
    ])

    if anomaly_type == "turbidity":
        reading["turbidity"] = round(random.uniform(6, 15), 2)

    elif anomaly_type == "ph":
        reading["ph"] = round(random.choice([random.uniform(4.5, 6), random.uniform(9, 10)]), 2)

    elif anomaly_type == "fluoride":
        reading["fluoride"] = round(random.uniform(1.6, 3.0), 2)

    elif anomaly_type == "coliform":
        reading["coliform"] = random.randint(20, 200)

    elif anomaly_type == "pressure":
        reading["pressure"] = round(random.choice([random.uniform(0.2, 0.8), random.uniform(6.5, 8)]), 2)

    elif anomaly_type == "do":
        reading["dissolved_oxygen"] = round(random.uniform(1.0, 3.5), 1)

    return reading


# -------- MAIN SIMULATION LOOP --------

def run_simulator():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(FETCH_NODES_QUERY)
        nodes = cursor.fetchall()

        print(f"[SIMULATOR] Loaded {len(nodes)} nodes")

        while True:
            now = datetime.now()
            batch = []

            for node_id, level in nodes:
                reading = generate_normal_reading(level)

                # ~3% chance of anomaly per cycle
                if random.random() < 0.03:
                    reading = inject_anomaly(reading)

                batch.append((
                    node_id,
                    now,
                    reading["turbidity"],
                    reading["ph"],
                    reading["fluoride"],
                    reading["coliform"],
                    reading["conductivity"],
                    reading["temperature"],
                    reading["dissolved_oxygen"],
                    reading["pressure"],
                    reading["flow_rate"]
                ))

            cursor.executemany(INSERT_SENSOR_QUERY, batch)
            conn.commit()

            print(f"[SIMULATOR] Inserted {len(batch)} readings @ {now.strftime('%H:%M:%S')}")

            time.sleep(random.uniform(5, 6))

    except KeyboardInterrupt:
        print("\n[SIMULATOR] Stopped by user")

    except Error as e:
        print("[ERROR]", e)

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# -------- RUN --------
if __name__ == "__main__":
    run_simulator()
