import json
import socket
import time
from datetime import datetime, timezone

import psutil
import requests

DEFAULT_CONFIG = {
    "backend_url": "http://127.0.0.1:8000/api/v1/ingest",
    "api_key": "TESTKEY123",
    "interval_sec": 0
}

def load_config():
    return DEFAULT_CONFIG
def collect_processes():
    procs = []
    for p in psutil.process_iter(attrs=['pid','ppid','name','cmdline','memory_info']):
        try:
            info = p.info
            if not info.get("pid") or not info.get("ppid"):
                continue  # skip invalid
            name = info.get("name") or "unknown"
            cpu = p.cpu_percent(None)
            mem = (info.get("memory_info").rss if info.get("memory_info") else p.memory_info().rss) / (1024*1024)
            cmd = " ".join(info.get("cmdline") or [])
            procs.append({
                "pid": int(info["pid"]),
                "ppid": int(info["ppid"]),
                "name": name,
                "cpu_percent": float(cpu),
                "memory_mb": float(mem),
                "cmdline": cmd[:8192]
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue  # last-resort safety
    return procs


def post_payload(cfg, processes):
    payload = {
        'hostname': socket.gethostname(),
        'captured_at': datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        'processes': processes
    }
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': cfg['api_key']
    }
    url = cfg['backend_url'].rstrip('/')
    if not url.endswith('/api/v1/ingest'):
        url = url + '/api/v1/ingest'
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    
    if r.status_code != 200:
        print("Serializer errors:", r.text)  # 👈 add this line

    r.raise_for_status()
    return r.json()


def main():
    cfg = load_config()
    interval = int(cfg.get('interval_sec', 0) or 0)
    while True:
        procs = collect_processes()
        try:
            res = post_payload(cfg, procs)
            print(f"Sent {len(procs)} processes. Snapshot ID: {res.get('snapshot_id')}")
        except Exception as e:
            print('Error sending data:', e)
        if interval <= 0:
            break
        time.sleep(interval)

if __name__ == '__main__':
    main()