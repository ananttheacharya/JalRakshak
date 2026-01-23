from pyvis.network import Network
import mysql.connector
from mysql.connector import Error


# -------- DB CONFIG --------
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "5568",
    "database": "jalrakshak"
}


# -------- COLORS --------
STATUS_COLOR = {
    "GREEN": "#2ecc71",
    "AMBER": "#f1c40f",
    "RED": "#e74c3c"
}

LEVEL_SIZE = {
    1: 40,   # Pump
    2: 25,   # Zone
    3: 15    # Colony
}


# -------- FETCH DATA --------
def fetch_data():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT n.node_id, n.hierarchy_level, n.pump, n.zone, n.colony,
               s.status, s.cwqi
        FROM nodes n
        LEFT JOIN node_status s ON n.node_id = s.node_id
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# -------- BUILD GRAPH --------
def build_mesh(rows):
    net = Network(
        height="100vh",
        width="100%",
        bgcolor="#0f0f0f",
        font_color="white",
        directed=True
    )

    net.force_atlas_2based(
        gravity=-40,
        central_gravity=0.01,
        spring_length=120,
        spring_strength=0.02,
        damping=0.4
    )

    # Add nodes
    for r in rows:
        color = STATUS_COLOR.get(r["status"], "#95a5a6")
        size = LEVEL_SIZE.get(r["hierarchy_level"], 10)

        label = (
            f"{r['node_id']}\n"
            f"CWQI: {round(r['cwqi'], 1) if r['cwqi'] is not None else 'N/A'}"
        )

        net.add_node(
            r["node_id"],
            label=label,
            color=color,
            size=size,
            title=f"""
                <b>{r['node_id']}</b><br>
                Level: {r['hierarchy_level']}<br>
                Pump: {r['pump']}<br>
                Zone: {r['zone']}<br>
                Colony: {r['colony']}<br>
                CWQI: {r['cwqi']}<br>
                Status: {r['status']}
            """
        )

    # Build lookup for hierarchy
    pump_nodes = {}
    zone_nodes = {}

    for r in rows:
        if r["hierarchy_level"] == 1:
            pump_nodes[r["pump"]] = r["node_id"]
        elif r["hierarchy_level"] == 2:
            zone_nodes[(r["pump"], r["zone"])] = r["node_id"]

    # Add edges
    for r in rows:
        if r["hierarchy_level"] == 2:
            parent = pump_nodes.get(r["pump"])
            if parent:
                net.add_edge(parent, r["node_id"], color="#555555")

        elif r["hierarchy_level"] == 3:
            parent = zone_nodes.get((r["pump"], r["zone"]))
            if parent:
                net.add_edge(parent, r["node_id"], color="#444444")

    return net


# -------- RUN DEMO --------
if __name__ == "__main__":
    print("[MESH] Fetching data...")
    rows = fetch_data()

    print(f"[MESH] Building mesh for {len(rows)} nodes...")
    net = build_mesh(rows)

    net.write_html("mesh.html", open_browser=True)

    print("[MESH] mesh.html generated — open it in your browser")
