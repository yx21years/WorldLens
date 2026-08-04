#!/usr/bin/env python3
"""Simple health check script for the backend."""
import requests
import sys

if __name__ == "__main__":
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        resp.raise_for_status()
        print(f"✓ Backend is healthy: {resp.json().get('status')}")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Health check failed: {e}", file=sys.stderr)
        sys.exit(1)
