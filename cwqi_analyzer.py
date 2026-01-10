import time
from datetime import datetime, timezone
import mysql.connector
from mysql.connector import Error

from cwqi import compute_cwqi


# -------- MySQL CONFIG --------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "5568",
    "database": "jalrakshak"
}


# -------- DB CONNECTION --------
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# -------- FETCH LATEST SENSOR READING PER NODE --------
LATEST_READING_QUERY = """
SELECT sr.node_id,
       sr.turbidity,
       sr.ph,
       sr.fluoride,
       sr.coliform,
       sr.conductivity,
       sr.temperature,
       sr.dissolved_oxygen,
       sr.pressure
FROM sensor_readings sr
JOIN (
    SELECT node_id, MAX(timestamp) AS latest_time
    FROM sensor_readings
    GROUP BY node_id
) latest
ON sr.node_id = latest.node_id
AND sr.timestamp = latest.latest_time
"""


# -------- UPSERT NODE STATUS --------
UPSERT_STATUS_QUERY = """
INSERT INTO node_status (
    node_id,
    last_updated,
    cwqi,
    status,
    reason,
    anomaly_detected
)
VALUES (%s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    last_updated = VALUES(last_updated),
    cwqi = VALUES(cwqi),
    status = VALUES(status),
    reason = VALUES(reason),
    anomaly_detected = VALUES(anomaly_detected)
"""


# -------- CONTINUOUS ANALYZER LOOP --------
def run_cwqi_analyzer(interval_seconds=5):
    print("[ANALYZER] CWQI analyzer started")

    try:
        while True:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(LATEST_READING_QUERY)
            readings = cursor.fetchall()

            print(f"[ANALYZER] Processing {len(readings)} nodes")

            now = datetime.now(timezone.utc)

            for row in readings:
                node_id = row["node_id"]

                reading = {
                    "turbidity": row["turbidity"],
                    "ph": row["ph"],
                    "fluoride": row["fluoride"],
                    "coliform": row["coliform"],
                    "conductivity": row["conductivity"],
                    "temperature": row["temperature"],
                    "dissolved_oxygen": row["dissolved_oxygen"],
                    "pressure": row["pressure"]
                }

                cwqi, status, reason = compute_cwqi(reading)
                anomaly = status in ("AMBER", "RED")

                cursor.execute(
                    UPSERT_STATUS_QUERY,
                    (
                        node_id,
                        now,
                        cwqi,
                        status,
                        reason,
                        anomaly
                    )
                )

            conn.commit()
            cursor.close()
            conn.close()

            print(f"[ANALYZER] Update complete @ {now.strftime('%H:%M:%S')}")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n[ANALYZER] Stopped by user")

    except Error as e:
        print("[ERROR]", e)


# -------- RUN --------
if __name__ == "__main__":
    run_cwqi_analyzer(interval_seconds=5)
