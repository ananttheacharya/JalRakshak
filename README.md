# JalRakshak

An IoT sensor simulation that monitors and analyzes Water Quality Parameters in city water pipelines and sends alerts to respective pumping stations and administrative zones in case of contamination and leakage.

## Project Structure
- `dashboard/`: Flask application for real-time visualization.
- `db/`: Database schema and seed data.
- `sensor_simulator.py`: Simulates IoT sensor data generation.
- `cwqi_analyzer.py`: Analyzes sensor data and generates alerts.

## Setup Instructions

### 1. Database Setup
Ensure you have MySQL/MariaDB installed and running.
Run the setup script to initialize the database, user, and load initial data:
```bash
python setup_db.py
```
You will be prompted for your MySQL root password.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
(Note: You may need to create a `requirements.txt` based on the imports: `flask`, `flask-socketio`, `eventlet`, `mysql-connector-python`, `geopy`, `folium` logic (if any used), etc.)

### 3. Run the System
Open three terminal windows:

**Terminal 1: Dashboard**
```bash
python dashboard/app.py
```
Visit `http://localhost:5000` in your browser.

**Terminal 2: Analyzer**
```bash
python cwqi_analyzer.py
```

**Terminal 3: Simulator**
```bash
python sensor_simulator.py
```

## Features
- **Real-time Map**: Visualizes nodes (pumps/zones/colonies) on a Leaflet map.
- **Mesh Network**: Interactive node graph.
- **Alerts**: Real-time alerting for contamination (CWQI > 100) or other anomalies.
- **Dark Mode**: Toggle available in the dashboard.
