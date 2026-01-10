from pyvis.network import Network
import mysql.connector
import time


# -------- DB CONFIG --------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "5568",
    "database": "jalrakshak"
}

REFRESH_SECONDS = 5
OUTPUT_FILE = "mesh.html"


STATUS_COLOR = {
    "GREEN": "#2ecc71",
    "AMBER": "#f1c40f",
    "RED": "#e74c3c"
}

LEVEL_SIZE = {
    1: 40,
    2: 25,
    3: 15
}


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

    for r in rows:
        color = STATUS_COLOR.get(r["status"], "#95a5a6")
        size = LEVEL_SIZE.get(r["hierarchy_level"], 10)

        label = f"{r['node_id']}\nCWQI: {round(r['cwqi'],1) if r['cwqi'] else 'N/A'}"

        net.add_node(
            r["node_id"],
            label=label,
            color=color,
            size=size,
            title=f"""
                <b>{r['node_id']}</b><br>
                Status: {r['status']}<br>
                CWQI: {r['cwqi']}<br>
                Pump: {r['pump']}<br>
                Zone: {r['zone']}<br>
                Colony: {r['colony']}
            """
        )

    pump_nodes = {}
    zone_nodes = {}

    for r in rows:
        if r["hierarchy_level"] == 1:
            pump_nodes[r["pump"]] = r["node_id"]
        elif r["hierarchy_level"] == 2:
            zone_nodes[(r["pump"], r["zone"])] = r["node_id"]

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


def inject_auto_refresh(html_file, seconds):
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    meta = f'<meta http-equiv="refresh" content="{seconds}">\n'
    html = html.replace("<head>", "<head>\n" + meta)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    print("[MESH] Auto-refresh mesh started")

    while True:
        rows = fetch_data()
        net = build_mesh(rows)

        net.write_html(OUTPUT_FILE, open_browser=False)
        inject_auto_refresh(OUTPUT_FILE, REFRESH_SECONDS)

        print("[MESH] Mesh updated")
        time.sleep(REFRESH_SECONDS)
