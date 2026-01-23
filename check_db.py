import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "5568"),
    "database": os.getenv("DB_NAME", "jalrakshak")
}

def check_alerts_table():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'alerts'")
        result = cursor.fetchone()
        if result:
            print("Table 'alerts' exists.")
            cursor.execute("DESCRIBE alerts")
            for x in cursor.fetchall():
                print(x)
        else:
            print("Table 'alerts' DOES NOT exist.")
            
            # Create it if it doesn't exist, as per plan (backup safety)
            print("Creating 'alerts' table...")
            create_query = """
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id INT AUTO_INCREMENT PRIMARY KEY,
                node_id VARCHAR(255),
                hierarchy_level INT,
                alert_level ENUM('AMBER', 'RED'),
                cwqi_value FLOAT,
                reason VARCHAR(255),
                detected_at DATETIME,
                resolved_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE
            )
            """
            cursor.execute(create_query)
            print("Table 'alerts' created.")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    check_alerts_table()
