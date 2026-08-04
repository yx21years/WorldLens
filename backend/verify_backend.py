#!/usr/bin/env python3
"""Simple server script that starts FastAPI and waits for health check."""
import subprocess
import time
import requests
import sys
import os

# Activate virtual environment (Windows)
if sys.platform == "win32":
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "Scripts", "activate")
else:
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "activate")

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # Start backend in a new process with venv activated
    if sys.platform == "win32":
        cmd = [f'call {venv_path} && python main.py', "--host", "127.0.0.1", "--port", "8000"]
        proc = subprocess.Popen(
            ["cmd.exe", "/C", f"{venv_path} && cd {backend_dir} && python main.py --host 127.0.0.1 --port 8000"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    else:
        proc = subprocess.Popen(
            [f"source {venv_path} && cd {backend_dir} && python main.py --host 127.0.0.1 --port 8000"],
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

    time.sleep(3)  # Wait for server to start

    # Try health check
    try:
        resp = requests.get("http://127.0.0.1:8000/health", timeout=5)
        print(f"✓ HEALTH CHECK PASSED: {resp.json()}")
        proc.terminate()
        proc.wait()
        sys.exit(0)
    except Exception as e:
        print(f"✗ HEALTH CHECK FAILED: {e}")
        print("Check backend logs above for errors.")
        proc.terminate()
        proc.wait()
        sys.exit(1)

if __name__ == "__main__":
    main()
