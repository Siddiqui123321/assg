# Process Monitoring Assignment

This project is a minimal end‑to‑end system monitor consisting of:
- Agent: Collects system and process metrics from a machine and posts snapshots to the backend.
- Backend (Django + DRF): Stores snapshots and serves a simple web UI and JSON APIs.
- Web UI: Shows System Details and a hierarchical Processes view per host, with search and auto‑refresh.

## Features
- Multiple hosts supported; each host authenticates with its own API key.
- Hosts are auto‑created on first ingest (no manual DB step required).
- System details: OS, CPU, cores/threads, RAM, storage, CPU frequency.
- Processes view: tree by PPID with expand/collapse, PID/PPID, CPU%, memory MB, search.
- Auto refresh with configurable interval.

## Requirements
- Python 3.10+ (tested on Windows 10/11)
- pip

## Quick Start (Windows PowerShell)
```powershell
# From repo root
cd backend

# 1) Create & activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Install deps
python -m pip install --upgrade pip
python -m pip install -r ../requirements.txt

# 3) Run DB migrations
python manage.py migrate

# 4) Start backend (http://127.0.0.1:8000)
python manage.py runserver
```

Open the UI: http://127.0.0.1:8000

## Run the Agent (same machine or remote)
```powershell
# From repo root
python agent/agent.py
```

By default the agent posts to http://127.0.0.1:8000/api/v1/ingest every 2s using the embedded config.

## Agent Configuration
The agent has an embedded DEFAULT_CONFIG in `agent/agent.py`:
```python
DEFAULT_CONFIG = {
    "backend_url": "http://127.0.0.1:8000/api/v1/ingest",
    "api_key": "TESTKEY123",
    "interval_sec": 2,           # post cadence
    "sample_sleep_ms": 200,      # CPU sampling window
    "include_cmdline": False,    # include process command lines
    "top_n_processes": None      # limit payload (e.g., 200)
}
```

Notes:
- CPU% comes from a two‑pass psutil sampling (prime, wait, read). Lower `sample_sleep_ms` for faster cycles; higher for smoother CPU%.
- For Windows, collecting full command lines can be slow; keep `include_cmdline=False` unless needed.

## Web UI Usage
- Left sidebar: refresh, auto toggle, interval (seconds), hosts list.
- Tabs: System Details, Processes Details.
- Processes tab: click ▶/▼ next to a process to expand/collapse children; use search to filter by name, PID, PPID.
- Auto refresh hits only the latest snapshot and processes endpoints at the chosen interval.

## API Overview
- POST `/api/v1/ingest` (Agent → Backend)
  - Header: `X-API-KEY: <host_api_key>`
  - Body: `{ hostname, captured_at, system_info, processes[] }`
  - Behavior: creates the `Host` automatically on first seen `hostname` + `api_key`; if the host exists, the same key must be used.
- GET `/api/v1/hosts` → `[ { hostname, last_seen } ]`
- GET `/api/v1/snapshots/latest?hostname=<host>` → `{ snapshot_id, captured_at, process_count, system{...} }`
- GET `/api/v1/snapshots/<id>/processes` → `[ { pid, ppid, name, cpu_percent, memory_mb, cmdline? } ]`

## Common Commands
- Run server: `python manage.py runserver`
- Run migrations: `python manage.py migrate`
- Create superuser (optional for admin): `python manage.py createsuperuser`
- Start agent: `python agent/agent.py`

## Troubleshooting
- CPU% is 0.0
  - psutil needs two reads; ensure the agent changes above are present and `sample_sleep_ms` > 50.
- UI doesn’t update
  - Check the Auto toggle and interval; ensure the agent is posting. Look at server console for `/ingest` requests.
- Requests every 5–10s
  - Controlled by UI Auto interval. Adjust the seconds field. The agent `interval_sec` should be equal or faster.
- High latency or large payloads
  - Disable `include_cmdline` and/or set `top_n_processes`.

## Project Structure
```
assg/
  agent/agent.py            # data collection client
  backend/                  # Django project
    backend/urls.py         # API + index routes
    monitor/                # app with models, views
    templates/index.html    # HTML, Tailwind CSS (CDN), Vanilla JavaScript.
  docs/README.md            # this file
```

## Notes and Assumptions
- Security is simplified: one API key per host. For production, use HTTPS, rotation, and auth hardening.
- SQLite is used for convenience. Swap to Postgres/MySQL for multi‑node scale.
- WebSockets could replace polling for true real‑time updates; current design uses polling for simplicity.

## License
For assignment/demo use.
