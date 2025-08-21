import psutil
import socket
import platform
import shutil
import requests
from datetime import datetime, timezone


# Embedded default config
DEFAULT_CONFIG = {
    "backend_url": "http://127.0.0.1:8000/api/v1/ingest",
    "api_key": "TESTKEY123"
}

def load_config():
    return DEFAULT_CONFIG

def collect_system_info():
    vm = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    cpu_freq = psutil.cpu_freq()

    return {
        "os": platform.platform(),
        "processor": platform.processor(),
        "cores": psutil.cpu_count(logical=False) or 0,
        "threads": psutil.cpu_count(logical=True) or 0,
        "ram_gb": round(vm.total / (1024**3), 2),
        "used_ram_gb": round((vm.total - vm.available) / (1024**3), 2),
        "available_ram_gb": round(vm.available / (1024**3), 2),
        "storage_total_gb": round(disk.total / (1024**3), 2),
        "storage_used_gb": round(disk.used / (1024**3), 2),
        "storage_free_gb": round(disk.free / (1024**3), 2),
        "cpu_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
    }

def collect_processes():
    processes = []
    for proc in psutil.process_iter(["pid", "ppid", "name", "cpu_percent", "memory_info", "cmdline"]):
        try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "ppid": info["ppid"],
                "name": info["name"] or "unknown",
                "cpu_percent": info["cpu_percent"],
                "memory_mb": round(info["memory_info"].rss / (1024*1024), 2) if info.get("memory_info") else 0.0,
                "cmdline": " ".join(info["cmdline"]) if info["cmdline"] else ""
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def main():
    config = load_config()
    backend_url = config["backend_url"]
    api_key = config["api_key"]

    payload = {
        "hostname": socket.gethostname(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "system_info": collect_system_info(),
        "processes": collect_processes()
    }

    headers = {"X-API-KEY": api_key}
    try:
        r = requests.post(backend_url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        print(f"Sent {len(payload['processes'])} processes + system info. Snapshot ID: {r.json().get('snapshot_id')}")
    except Exception as e:
        print("Error sending data:", e)

if __name__ == "__main__":
    main()
