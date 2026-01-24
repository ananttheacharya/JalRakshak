import subprocess
import time
import os
import sys
import threading
import urllib.request
import zipfile
import re


NGROK_DOMAIN = ""      
NGROK_AUTH_TOKEN = "" 

# Components configuration
COMPONENTS = [
    {"name": "Simulator", "cmd": ["python", "sensor_simulator.py"], "cwd": "."},
    {"name": "Analyzer", "cmd": ["python", "cwqi_analyzer.py"], "cwd": "."},
    {"name": "Dashboard", "cmd": ["python", "dashboard/app.py"], "cwd": "."},
]

NGROK_URL = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
NGROK_EXE = "ngrok.exe"

REQUIRED_PACKAGES = [
    "flask",
    "flask-socketio",
    "mysql-connector-python",
    "pyvis",
    "geopy",
    "eventlet",
    "python-dotenv"
]

def install_packages():
    print(f"[ MVP ] Verifying dependencies...")
    for package in REQUIRED_PACKAGES:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL)
        except Exception as e:
            print(f"[ERROR] Failed to install {package}: {e}")




def download_ngrok():
    if not os.path.exists(NGROK_EXE):
        print(f"[ MVP ] Downloading {NGROK_EXE} from Ngrok...")
        try:
            zip_path = "ngrok.zip"
            urllib.request.urlretrieve(NGROK_URL, zip_path)
            print("[ MVP ] Unzipping...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)
            print("[ MVP ] Download complete.")
        except Exception as e:
            print(f"[ERROR] Failed to download ngrok: {e}")
            print("Please download it manually from ngrok.com and place it in this folder.")
            sys.exit(1)
    else:
        print(f"[ MVP ] Found {NGROK_EXE}")

def configure_ngrok_auth():
    if NGROK_AUTH_TOKEN:
        print("[ MVP ] Applying Ngrok Auth Token...")
        subprocess.run([NGROK_EXE, "config", "add-authtoken", NGROK_AUTH_TOKEN], check=False)

def stream_logs(name, process):
    """
    Reads stdout of a subprocess, filters noisy lines, and prints the rest.
    """
    try:
        for line in iter(process.stdout.readline, b''):
            line_str = line.decode('utf-8', errors='ignore').strip()
            
            # --- AGGRESSIVE NOISE FILTER ---
            # Only show vital info or errors.
            is_error = "error" in line_str.lower() or "exception" in line_str.lower() or "failed" in line_str.lower()
            is_link = "http" in line_str and "ngrok" in line_str
            
            if not (is_error or is_link):
                continue
            
            print(f"[{name}] {line_str}")
    except Exception:
        pass

def run_all():
    processes = []
    
    print("\n" + "="*60)
    print("   JALRAKSHAK MVP LAUNCHER (NGROK EDITION)")
    print("   Simulator + Analyzer + Dashboard + Persistent Tunnel")
    print("="*60 + "\n")

    # 1. Setup Dependencies & Env
    install_packages()

    # Load .env now that we know python-dotenv is installed
    try:
        from dotenv import load_dotenv
        load_dotenv()
        global NGROK_DOMAIN, NGROK_AUTH_TOKEN
        # Prioritize env vars
        if not NGROK_DOMAIN: 
            NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "")
        if not NGROK_AUTH_TOKEN:
            NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN", "")
            
    except ImportError:
        print("[ WARN ] python-dotenv not loaded. Configuration might fail.")


    # 2. Setup Ngrok

    download_ngrok()
    configure_ngrok_auth()

    try:
        # 2. Start Python Components
        for comp in COMPONENTS:
            print(f"[ MVP ] Starting {comp['name']}...")
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            p = subprocess.Popen(
                comp["cmd"],
                cwd=comp["cwd"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env
            )
            processes.append(p)
            
            t = threading.Thread(target=stream_logs, args=(comp['name'], p))
            t.daemon = True
            t.start()
            
            time.sleep(1)

        print("[ MVP ] Components started. Waiting for dashboard...")
        time.sleep(3)

        # 3. Start Ngrok Tunnel
        print("[ MVP ] Starting Ngrok Tunnel...")
        
        tunnel_cmd = [NGROK_EXE, "http", "5000"]
        if NGROK_DOMAIN:
            tunnel_cmd.append(f"--domain={NGROK_DOMAIN}")
        else:
            print("[WARN] No Static Domain configured. Link will be random.")

        # Ngrok is interactive, so we can't easily capture the URL from stdout in real-time
        # accurately without using their API or log parsing. 
        # Simpler: Run it with --log=stdout so we can parse it.
        tunnel_cmd.append("--log=stdout")

        tunnel_process = subprocess.Popen(
            tunnel_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(tunnel_process)

        # Watch output
        url_found = False
        print("\n" + "-"*60)
        print("Waiting for Public URL...")
        print("-"*60 + "\n")
        
        while True:
            line = tunnel_process.stdout.readline()
            if not line:
                break
            
            line_str = line.decode('utf-8', errors='ignore').strip()
            
            # Ngrok log format: "url=https://..."
            match = re.search(r'url=(https://[^\s]+)', line_str)
            if match:
                public_url = match.group(1)
                print("\n" + "*"*60)
                print(f"   SUCCESS! YOUR PERMANENT LINK IS LIVE:")
                print(f"   {public_url}")
                print("*"*60 + "\n")
                url_found = True
            elif "ERR_NGROK" in line_str:
                 print(f"[NGROK ERROR] {line_str}")

    except KeyboardInterrupt:
        print("\n[ MVP ] Stopping all services...")
    finally:
        for p in processes:
            try:
                p.terminate()
            except:
                pass
        print("[ MVP ] Cleanup complete.")

if __name__ == "__main__":
    run_all()
