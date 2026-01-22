from flask import Flask, render_template, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json

app = Flask(__name__)

# MySQL CONFIG
DB_CONFIG = {
    "host": "localhost",
    "user": "jalrakshak",
    "password": "jalrakshak123",
    "database": "jalrakshak"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/nodes")
def get_nodes():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetch latest status for all nodes
        query = """
        SELECT n.node_id, n.hierarchy_level, n.pump, n.zone, n.colony, n.latitude, n.longitude,
               ns.cwqi, ns.status, ns.reason, ns.last_updated
        FROM nodes n
        LEFT JOIN node_status ns ON n.node_id = ns.node_id
        """
        cursor.execute(query)
        nodes = cursor.fetchall()
        
        # Format for vis.js or frontend usage
        # We need to map this to the format expected by the visualizer
        # For now sending raw data, frontend will parse
        return jsonify(nodes)
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.route("/api/alerts")
def get_alerts():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetch active alerts first, then recent resolved ones
        # Use a simpler query for the log
        # Fetch active alerts
        query_active = """
        SELECT alert_id, node_id, hierarchy_level, alert_level, cwqi_value, reason, detected_at, is_active
        FROM alerts
        WHERE is_active = 1
        ORDER BY detected_at DESC
        """
        cursor.execute(query_active)
        active_alerts = cursor.fetchall()
        
        # Fetch recently resolved alerts (last 10)
        query_resolved = """
        SELECT alert_id, node_id, hierarchy_level, alert_level, cwqi_value, reason, detected_at, resolved_at, is_active
        FROM alerts
        WHERE is_active = 0
        ORDER BY resolved_at DESC
        LIMIT 10
        """
        cursor.execute(query_resolved)
        resolved_alerts = cursor.fetchall()
        
        return jsonify({
            "active": active_alerts,
            "resolved": resolved_alerts
        })
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
