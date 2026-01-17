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
       n.hierarchy_level,
       sr.turbidity,
       sr.ph,
       sr.fluoride,
       sr.coliform,
       sr.conductivity,
       sr.temperature,
       sr.dissolved_oxygen,
       sr.pressure
FROM sensor_readings sr
JOIN nodes n ON sr.node_id = n.node_id
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


# -------- ALERT QUERIES --------
GET_ACTIVE_ALERT_QUERY = """
SELECT alert_id, alert_level
FROM alerts
WHERE node_id = %s AND is_active = 1
LIMIT 1
"""

INSERT_ALERT_QUERY = """
INSERT INTO alerts (
    node_id, hierarchy_level, alert_level, cwqi_value,
    reason, detected_at, is_active
) VALUES (%s, %s, %s, %s, %s, %s, 1)
"""

RESOLVE_ALERT_QUERY = """
UPDATE alerts
SET is_active = 0, resolved_at = %s
WHERE alert_id = %s
"""

RESOLVE_ALL_ALERTS_QUERY = """
UPDATE alerts
SET is_active = 0, resolved_at = %s
WHERE node_id = %s AND is_active = 1
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
                hierarchy_level = row["hierarchy_level"]

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

                # -------- ALERT LOGIC --------
                # Check for existing active alerts
                cursor.execute(GET_ACTIVE_ALERT_QUERY, (node_id,))
                active_alert = cursor.fetchone()

                if status == "GREEN":
                    # Condition is normal, resolve any active alerts
                    if active_alert:
                        print(f"[ALERT] Resolving alert for {node_id}")
                        cursor.execute(RESOLVE_ALL_ALERTS_QUERY, (now, node_id))
                
                elif status in ("AMBER", "RED"):
                    # Abnormal condition
                    if not active_alert:
                        # No active alert, create new one
                        print(f"[ALERT] Raising {status} alert for {node_id}")
                        cursor.execute(INSERT_ALERT_QUERY, (
                            node_id, hierarchy_level, status, cwqi, reason, now
                        ))
                    else:
                        # Active alert exists. Check if severity changed.
                        current_alert_level = active_alert['alert_level']
                        if current_alert_level != status:
                            # Severity changed (e.g. AMBER -> RED or RED -> AMBER)
                            # Resolve old, create new
                            print(f"[ALERT] Updating alert level {current_alert_level} -> {status} for {node_id}")
                            cursor.execute(RESOLVE_ALERT_QUERY, (now, active_alert['alert_id']))
                            cursor.execute(INSERT_ALERT_QUERY, (
                                node_id, hierarchy_level, status, cwqi, reason, now
                            ))
                        # else: same severity, do nothing

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
