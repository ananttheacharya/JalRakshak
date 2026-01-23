# JalRakshak MVP

JalRakshak is a Smart Water Management System designed to simulate, monitor, and analyze water quality parameters (like CWQI) across a city's pipeline network.

## 🚀 One-Click Launch (Recommended)

This project includes a fully automated orchestrator that sets up the environment, connects to the database, launches all components, and creates a persistent public tunnel.

1.  **Configure `.env`**:
    Ensure the `.env` file in this directory has your correct Database credentials and Ngrok configuration.
    ```ini
    DB_HOST=127.0.0.1
    DB_USER=root
    DB_PASSWORD=your_password
    NGROK_AUTH_TOKEN=your_token
    NGROK_DOMAIN=your_domain.ngrok-free.app
    ```

2.  **Run the Orchestrator**:
    ```bash
    python run_mvp.py
    ```
    This will:
    *   Install required Python packages automatically.
    *   Download Ngrok (if missing).
    *   Start the **Sensor Simulator** (generates data).
    *   Start the **CWQI Analyzer** (processes data & alerts).
    *   Start the **Dashboard** (visualizes specific node data).
    *   Establish a **Persistent Public URL** via Ngrok.

## 📂 Project Architecture

*   **`dashboard/app.py`**: The Flask web server serving the UI. Listens on port 5000.
*   **`sensor_simulator.py`**: Simulates IoT nodes (Pumping Stations, Zonal Tanks, Residential Colonies) and generates flow/quality data.
*   **`cwqi_analyzer.py`**: Real-time analysis engine that computes Canadian Water Quality Index (CWQI) and generates alerts.
*   **`run_mvp.py`**: Orchestration script to run everything together.

## 🛠 Manual Setup (Developer)

If you prefer to run components individually:

1.  **Install Dependencies**:
    ```bash
    pip install flask flask-socketio mysql-connector-python pyvis geopy eventlet python-dotenv
    ```

2.  **Database Setup**:
    Run `setup_db.py` to initialize the schema and users.

3.  **Run Components**:
    Open 3 separate terminals:
    ```bash
    # Terminal 1
    python sensor_simulator.py

    # Terminal 2
    python cwqi_analyzer.py

    # Terminal 3
    python dashboard/app.py
    ```

## 🐛 Troubleshooting

*   **MySQL Error 10060 (Timeout)**:
    *   The scripts have built-in retry logic. If this persists, check if your MySQL server is running and accessible at `127.0.0.1`.
*   **Ngrok Error**:
    *   Ensure your `NGROK_AUTH_TOKEN` in `.env` is correct.
    *   If the static domain fails, leave `NGROK_DOMAIN` empty in `.env` to get a random URL.

## 🔐 Security Note

*   This project uses a `.env` file to manage secrets. **Do not commit `.env` to public repositories.**
*   The `.gitignore` is configured to exclude sensitive files.
