import psutil
import socket
import platform
import shutil
import requests
from datetime import datetime, timezone


# Embedded default config
DEFAULT_CONFIG = {
    "backend_url": "http://127.0.0.1:8000/api/v1/ingest",
    "api_key": "TESTKEY123",
    # How often to post snapshots (seconds)
    "interval_sec": 2,
    # Sleep used between priming and reading cpu_percent (milliseconds)
    "sample_sleep_ms": 200,
    # Whether to include full command lines (expensive on Windows)
    "include_cmdline": False,
    # If set, only keep top N processes by memory to reduce payload
    "top_n_processes": None,
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

def collect_processes(include_cmdline: bool = False, sample_sleep_ms: int = 200, top_n: int | None = None):
    # First pass: prime CPU counters for each process (returns 0.0 initially)
    procs = []
    for p in psutil.process_iter(["pid", "ppid", "name"]):
        try:
            p.cpu_percent(None)
            procs.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Small sampling interval to measure CPU deltas
    sleep_secs = max(0.05, (sample_sleep_ms or 200) / 1000.0)
    __import__('time').sleep(sleep_secs)

    # Second pass: read cpu_percent and memory
    processes = []
    for p in procs:
        try:
            with p.oneshot():
                info = {
                    "pid": p.pid,
                    "ppid": p.ppid(),
                    "name": p.name() or "unknown",
                    "cpu_percent": float(p.cpu_percent(None)),
                    "memory_mb": round(p.memory_info().rss / (1024 * 1024), 2),
                }
                if include_cmdline:
                    try:
                        cmd = p.cmdline()
                        info["cmdline"] = " ".join(cmd) if cmd else ""
                    except Exception:
                        info["cmdline"] = ""
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Optionally down-select to reduce payload size and time
    if top_n:
        processes.sort(key=lambda x: x["memory_mb"], reverse=True)
        processes = processes[: int(top_n)]
    return processes

def main():
    import time
    config = load_config()
    backend_url = config["backend_url"]
    api_key = config["api_key"]
    interval = max(1, int(config.get("interval_sec", 2)))
    sample_sleep_ms = int(config.get("sample_sleep_ms", 200))
    include_cmdline = bool(config.get("include_cmdline", False))
    top_n = config.get("top_n_processes")

    headers = {"X-API-KEY": api_key}
    hostname = socket.gethostname()

    print(f"Agent started for {hostname}. Posting every {interval}s to {backend_url}.")
    try:
        while True:
            t0 = time.time()
            payload = {
                "hostname": hostname,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "system_info": collect_system_info(),
                "processes": collect_processes(include_cmdline=include_cmdline, sample_sleep_ms=sample_sleep_ms, top_n=top_n),
            }
            try:
                r = requests.post(backend_url, json=payload, headers=headers, timeout=10)
                r.raise_for_status()
                print(f"Sent {len(payload['processes'])} processes. Snapshot ID: {r.json().get('snapshot_id')}")
            except Exception as e:
                print("Error sending data:", e)

            # Sleep remaining time in the interval
            dt = time.time() - t0
            time.sleep(max(0, interval - dt))
    except KeyboardInterrupt:
        print("Agent stopped.")

if __name__ == "__main__":
    main()
