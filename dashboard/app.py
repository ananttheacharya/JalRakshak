import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json
import time

import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
socketio = SocketIO(app, async_mode='eventlet')

# MySQL CONFIG
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "5568"),
    "database": os.getenv("DB_NAME", "jalrakshak")
}

def get_connection():
    attempts = 0
    while attempts < 3:
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            attempts += 1
            print(f"[DB] Connection failed (Attempt {attempts}/3): {e}")
            time.sleep(1)
    raise Error("Failed to connect to database after 3 attempts")

def fetch_nodes():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT n.node_id, n.hierarchy_level, n.pump, n.zone, n.colony, n.latitude, n.longitude,
               ns.cwqi, ns.status, ns.reason, ns.last_updated
        FROM nodes n
        LEFT JOIN node_status ns ON n.node_id = ns.node_id
        """
        cursor.execute(query)
        nodes = cursor.fetchall()
        
        # Convert datetime objects to string and decimals to float
        for node in nodes:
            if node['last_updated']:
                node['last_updated'] = node['last_updated'].isoformat()
            if node['latitude']: node['latitude'] = float(node['latitude'])
            if node['longitude']: node['longitude'] = float(node['longitude'])
            if node['cwqi']: node['cwqi'] = float(node['cwqi'])
                
        cursor.close()
        conn.close()
        return nodes
    except Error as e:
        print(f"Error fetching nodes: {e}")
        return []

def fetch_alerts():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query_active = """
        SELECT alert_id, node_id, hierarchy_level, alert_level, cwqi_value, reason, detected_at, is_active
        FROM alerts
        WHERE is_active = 1
        ORDER BY detected_at DESC
        """
        cursor.execute(query_active)
        active_alerts = cursor.fetchall()
        
        query_resolved = """
        SELECT alert_id, node_id, hierarchy_level, alert_level, cwqi_value, reason, detected_at, resolved_at, is_active
        FROM alerts
        WHERE is_active = 0
        ORDER BY resolved_at DESC
        LIMIT 10
        """
        cursor.execute(query_resolved)
        resolved_alerts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects and decimals
        for a in active_alerts:
            if a['detected_at']: a['detected_at'] = a['detected_at'].isoformat()
            if a['cwqi_value']: a['cwqi_value'] = float(a['cwqi_value'])
        
        for a in resolved_alerts:
            if a['detected_at']: a['detected_at'] = a['detected_at'].isoformat()
            if a['resolved_at']: a['resolved_at'] = a['resolved_at'].isoformat()
            if a['cwqi_value']: a['cwqi_value'] = float(a['cwqi_value'])
            
        return {"active": active_alerts, "resolved": resolved_alerts}
    except Error as e:
        print(f"Error fetching alerts: {e}")
        return {"active": [], "resolved": []}

def background_thread():
    """Background thread to push updates."""
    print("Background thread started")
    while True:
        # Rate limit updates
        socketio.sleep(2)
        
        # Fetch data
        nodes = fetch_nodes()
        alerts = fetch_alerts()
        
        # Broadcast updates
        socketio.emit('update_nodes', nodes)
        socketio.emit('update_alerts', alerts)

@app.route("/")
def index():
    return render_template("index.html")

# Keep API endpoints for initial load if needed
@app.route("/api/nodes")
def get_nodes():
    return jsonify(fetch_nodes())

@app.route("/api/alerts")
def get_alerts():
    return jsonify(fetch_alerts())

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('update_nodes', fetch_nodes())
    emit('update_alerts', fetch_alerts())

if __name__ == "__main__":
    # Start background task
    socketio.start_background_task(background_thread)
    socketio.run(app, debug=False, host="0.0.0.0", port=5000)
