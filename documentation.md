# JalRakshak: A Smart Water Quality Monitoring & Orchestration System
**Technical Documentation & Research Paper**

**Abstract**
JalRakshak is a comprehensive Smart Water Management System designed to simulate, monitor, and analyze water quality parameters across a hierarchical city pipeline network. The system calculates the Centralized Water Quality Index (CWQI) in real-time, simulating contaminant propagation through hydraulic systems (Pumping Stations → Zonal Tanks → Residential Colonies) with a deterministic time-delay model. Architecture is built on a Python-based microservices pattern, utilizing a MySQL relational database for persistence, a Flask-based visualization dashboard, and `ngrok` for secure public tunneling. The system features a custom stochastic sensor simulator that generates realistic hydrological data (Turbidity, pH, Fluoride, Coliform, Conductivity, Temperature, DO, Pressure, Flow Rate) and an autonomous `cwqi_analyzer` that processes 8-parameter readings to detect anomalies (Green/Amber/Red status) and manage alert lifecycles. This document provides an exhaustive technical breakdown of the system's algorithms, database schema, and operational workflows.

---

## 1. System Architecture

The JalRakshak ecosystem is composed of four distinct, loosely coupled components that interact via a shared MySQL database.

### 1.1 Component Overview

1.  **Sensor Simulator (`sensor_simulator.py`)**:
    *   **Role**: Acts as the data ingress layer, simulating IoT devices attached to water infrastructure.
    *   **Behavior**: Generates synthetic sensor readings every 5 seconds for all registered nodes. It implements a stochastic contamination model, introducing random pollutants and propagating them downstream based on a parent-child hierarchy map.
    *   **Key Logic**: Uses `random.uniform()` for continuous variables and `random.randint()` for discrete ones (Coliform).

2.  **CWQI Analyzer (`cwqi_analyzer.py`)**:
    *   **Role**: The compute engine. It polls the database for the latest sensor readings.
    *   **Behavior**: Computes the CWQI score using a Weighted Arithmetic Index method. It determines the operational status of each node and manages the `alerts` table (creating, updating severity, or resolving alerts).
    *   **Cycle**: Runs on a 5-second infinite loop.

3.  **Database Layer (MySQL)**:
    *   **Role**: Central state store.
    *   **Persistence**: Stores static infrastructure data (`nodes`), high-frequency time-series data (`sensor_readings`), processed state (`node_status`), and event logs (`alerts`).

4.  **Dashboard & Orchestrator**:
    *   **Dashboard (`dashboard/app.py`)**: A Flask web application providing a real-time visualization of the network graph and node health.
    *   **Orchestrator (`run_mvp.py`)**: A unified entry point that manages the lifecycle of all subprocesses (Simulator, Analyzer, Dashboard, Ngrok), handling dependency installation, environment configuration, and graceful shutdowns.

### 1.2 Hierarchy Model (`nodes` table)
The system models the water network as a directed tree graph with 3 levels:
*   **Level 1 (Pumping Stations)**: Root nodes. Sources of water.
*   **Level 2 (Zonal Tanks)**: Intermediate storage. Children of Level 1.
*   **Level 3 (Residential Colonies)**: End measurement points. Children of Level 2.

---

## 2. Algorithms & Mathematical Models

### 2.1 Centralized Water Quality Index (CWQI)
The CWQI is computed using the Weighted Arithmetic Water Quality Index method. The formula is:

$$ CWQI = \frac{\sum_{i=1}^{n} W_i \cdot Q_i}{\sum_{i=1}^{n} W_i} $$

Where:
*   $W_i$ is the unit weight for the $i$-th parameter.
*   $Q_i$ is the quality rating (normalization) for the $i$-th parameter.

#### 2.1.1 Parameter Weights ($W_i$)
Weights are defined in `cwqi.py` based on public health impact:

| Parameter | Weight ($W_i$) |
| :--- | :--- |
| Coliform | 0.25 (Critical) |
| Turbidity | 0.15 |
| pH | 0.15 |
| Fluoride | 0.10 |
| Conductivity | 0.10 |
| Dissolved Oxygen (DO) | 0.10 |
| Pressure | 0.10 |
| Temperature | 0.05 |

#### 2.1.2 Normalization Functions ($Q_i$)
Each parameter raw value ($V$) is normalized to a score ($Q$) between 0 and 100.

1.  **Turbidity (NTU)**:
    *   If $V \le 1$: $Q = 100$
    *   If $1 < V \le 5$: $Q = 100 - 20(V - 1)$
    *   If $V > 5$: $Q = 0$

2.  **pH**:
    *   Ideal range: 6.5 - 8.5 ($Q=100$)
    *   Deviation penalty: $Q = \max(0, 100 - |V - 7.0| \times 50)$

3.  **Fluoride (mg/L)**:
    *   $V \le 1.0$: $Q=100$
    *   $1.0 < V \le 1.5$: $Q = 100 - (V - 1.0) \times 100$
    *   $V > 1.5$: $Q=0$

4.  **Coliform (CFU/100ml)**:
    *   $V = 0$: $Q=100$
    *   $0 < V \le 10$: $Q=50$
    *   $V > 10$: $Q=0$
    *   *Hard Rule*: If Coliform > 0, overall Status is forced to **RED**.

5.  **Conductivity ($\mu S/cm$)**:
    *   $V \le 500$: $Q=100$
    *   $500 < V \le 1500$: Linear decay to 0.

6.  **Dissolved Oxygen (mg/L)**:
    *   $V \ge 6$: $Q=100$
    *   $4 \le V < 6$: Linear decay.
    *   $V < 4$: $Q=0$

7.  **Pressure (Bar)**:
    *   $2 \le V \le 5$: $Q=100$
    *   $V \in [1, 2)$ or $(5, 6]$: $Q=50$
    *   Else: $Q=0$

8.  **Temperature (°C)**:
    *   $20 \le V \le 30$: $Q=100$
    *   $30 < V \le 35$: Linear decay.

#### 2.1.3 Status Classification
*   **GREEN**: $CWQI \ge 80$ (Safe)
*   **AMBER**: $50 \le CWQI < 80$ (Caution)
*   **RED**: $CWQI < 50$ or Coliform > 0 (Unsafe)

---

### 2.2 Contamination Propagation Model (`sensor_simulator.py`)
To mimic real-world fluid dynamics, the simulator implements a time-delay propagation algorithm.

1.  **Trigger Event**:
    *   **Spontaneous Contamination**: In every 5-second cycle, there is a **1% probability** (`random.random() < 0.01`) that a random Level 1 (Pump) node will be contaminated.
    *   **Severity**: Randomly chosen between 'AMBER' (minor drift) or 'RED' (major spike).

2.  **Downstream Propagation**:
    *   When a node is contaminated, it is added to a `CONTAMINATION_QUEUE`.
    *   **Delay Logic**: The contamination does not appear instantly at child nodes. The system adds a **20-second delay** (`timedelta(seconds=20)`) for every hop in the hierarchy.
    *   *Flow*: Pump (T=0) --> Zone (T+20s) --> Colony (T+40s).

3.  **Sensor Values during Contamination**:
    *   **AMBER Scenario**:
        *   Turbidity: 4.5 - 6.0 NTU
        *   Coliform: 10 - 50 CFU
    *   **RED Scenario**:
        *   Turbidity: 10.0 - 25.0 NTU
        *   Coliform: 100 - 500 CFU
        *   pH: 5.5 - 6.0 (Acidic)

---

## 3. Database Schema (`schema.sql`)

The system uses a normalized MySQL schema.

### 3.1 `nodes`
Stores the static infrastructure graph.
*   `node_id` (PK, VARCHAR): Unique identifier.
*   `hierarchy_level` (INT): 1, 2, or 3.
*   `pump`, `zone`, `colony`: Dimensional attributes for grouping.
*   `latitude`, `longitude`: Geolocation for map visualization.

### 3.2 `sensor_readings`
High-volume table modifying at $N \times 12$ rows per minute (where N is node count).
*   `reading_id` (PK, BIGINT): Auto-increment.
*   `node_id` (FK): Links to `nodes`.
*   `timestamp`: DATETIME.
*   `turbidity`, `ph`, `fluoride`, ...: FLOAT/INT columns for each parameter.
*   **Indexes**: `idx_node_time` (`node_id`, `timestamp`) enables efficient retrieval of the "latest" reading.

### 3.3 `node_status`
The "Current State" table, updated by `cwqi_analyzer.py`.
*   `cwqi` (FLOAT): Latest calculated index.
*   `status`: ENUM('GREEN', 'AMBER', 'RED').
*   `anomaly_detected` (TINYINT): Boolean flag.
*   `reason`: Text explanation (e.g., "coliform degraded").

### 3.4 `alerts`
Event log for tracking incident lifecycles.
*   `alert_id` (PK): Unique ID.
*   `alert_level`: Severity of the alert.
*   `is_active` (BOOL): 1 if ongoing, 0 if resolved.
*   `detected_at`, `resolved_at`: Timespans.

---

## 4. Orchestration & Implementation Details

### 4.1 The Orchestrator (`run_mvp.py`)
This script automates the entire deployment pipeline.

1.  **Environment Setup**:
    *   Parses `.env` for `DB_USER`, `DB_PASSWORD`, `NGROK_AUTH_TOKEN`.
    *   **Constraint**: The process fails if `NGROK_AUTH_TOKEN` is missing, as the public tunnel is a core requirement.

2.  **Dependency Management**:
    *   Automatically runs `pip install` for `flask`, `mysql-connector-python`, `geopy`, etc.

3.  **Process Management**:
    *   Uses Python's `subprocess.Popen` to spawn independent processes for `sensor_simulator.py`, `cwqi_analyzer.py`, and `dashboard/app.py`.
    *   **Platform Specifics**: On Windows, it handles the `ngrok.exe` binary directly; on Linux/Mac, it expects `ngrok` in PATH.

4.  **Ngrok Tunneling**:
    *   Spawns Ngrok as a background process exposing port 5000 (`ngrok http 5000`).
    *   Queries `http://127.0.0.1:4040/api/tunnels` to retrieve the public URL dynamically and prints it to the console.

### 4.2 Data Analysis Loop (`cwqi_analyzer.py`)
The analyzer runs an infinite loop with `time.sleep(5)` interval.

1.  **Read Step**:
    *   Executes `LATEST_READING_QUERY` which performs an INNER JOIN on a subquery finding `MAX(timestamp)` for each `node_id`. This ensures only the absolute latest data is processed.
    
2.  **Compute & Write Step**:
    *   Calls `compute_cwqi(reading)` for every node.
    *   Performs an `INSERT ... ON DUPLICATE KEY UPDATE` into `node_status`.

3.  **Alert Logic**:
    *   **Green Transition**: If current status is GREEN and an active alert exists, executes `RESOLVE_ALL_ALERTS_QUERY`.
    *   **Severity Escalation**: If current status is RED but active alert is AMBER, it resolves the AMBER alert and creates a new RED alert.
    *   **New Alert**: If current status is non-GREEN and no active alert exists, executes `INSERT_ALERT_QUERY`.

---

## 5. Deployment Instructions

### 5.1 Prerequisites
*   Python 3.8+
*   MySQL Server 8.0+ running on `127.0.0.1:3306`.
*   Ngrok Account (Auth Token).

### 5.2 Setup Steps
1.  **Database**: Run `python setup_db.py`. This creates the `jalrakshak` user and seeds initial node data.
2.  **Configuration**: Create `.env` file:
    ```ini
    DB_HOST=127.0.0.1
    DB_USER=root
    DB_PASSWORD=your_mysql_root_password
    NGROK_AUTH_TOKEN=your_auth_token
    ```
3.  **Launch**: Execute `python run_mvp.py`. The system will auto-install dependencies and provide a public Dashboard URL (e.g., `https://random-id.ngrok-free.app`).

---

## 6. References & Dependencies
*   **MySQL Connector/Python**: Used for detailed database interaction and connection pooling (retry logic implemented).
*   **Flask & Flask-SocketIO**: Serves the frontend dashboard.
*   **PyVis**: (Optional) Used for graph visualization in auxiliary scripts.
*   **Geopy**: Used for distance calculations during initial node population.
