# 🛸 Dali C2x2: Professional Orchestration Framework

Dali C2x2 is a lightweight, job-oriented Command & Control (C2) framework designed for fleet management, orchestration, and security auditing. It follows a clean separation between the **Control Plane (Server)** and the **Managed Nodes (Agents)**.

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-red.svg)

## 🏗️ Architecture

- **Control Server**: FastAPI-powered backend with SQLite persistence and a modern Web GUI.
- **Managed Node (Agent)**: Asynchronous Python agent (compilable to a standalone `.exe`) that polls the server for jobs.
- **Operator Dashboard**: A premium, web-based UI for real-time node monitoring and job orchestration.

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+ installed on the Host machine.
- `pip` for package management.

### 2. Installation

Clone the repository and install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Start the Control Plane (Server)

```bash
python -m server.main
```

The dashboard will be available at: **`http://localhost:8000`**

### 4. Deploy Managed Nodes (Agents)

**Option A: Run via Python (Development)**

```bash
# On the target machine
export C2_SERVER_URL="http://YOUR_SERVER_IP:8000"
python -m agent.agent
```

**Option B: Build Standalone Executable (Production)**
If the target machine doesn't have Python, compile the agent into a single `.exe`:

```bash
python build_agent.py
```

Find the output in `dist/c2_agent.exe` and deploy it to the target Windows VM.

---

## 🛠️ Features

- **Job Orchestration**: Queue shell commands or system telemetry gathering tasks.
- **Auto-Discovery**: Nodes automatically report OS version, machine name, and user metadata.
- **Audit Trails**: Every job is tracked with unique IDs and precise timestamps (`pending` -> `leased` -> `completed`).
- **Persistence**: Full SQLite backend ensures no data is lost between server restarts.
- **No-Console Mode**: Built-in support for background execution on Windows targets.

---

## 🕹️ Using the Dashboard

1. **Inventory**: View all registered nodes in the sidebar. Green indicates a node has been seen recently.
2. **Node Control**: Select a node to view its specific job history and hardware telemetry.
3. **Queue Jobs**: Use the drop-down to select a job type (Shell/Sysinfo), enter your payload, and hit **Submit Job**.
4. **Live Execution**: Watch the "Job Orchestration History" table update as the agent leases and completes the task.

---

## 📂 Project Layout

```text
c2-framework/
├── server/             # FastAPI Backend & Database Logic
│   ├── templates/      # Dashboard HTML
│   ├── static/         # CSS & Assets
│   ├── models.py       # DB Schema
│   └── store.py        # Persistence Layer
├── agent/              # Node Execution Logic
│   ├── agent.py        # Main Loop & Communication
│   └── executor.py     # Job Handlers (Shell, Sysinfo)
├── shared/             # Cross-tier Pydantic Schemas
└── dist/               # Compiled executables (Generated)
```

## ⚖️ Legal Disclaimer

This software is intended for **authorized security testing and educational purposes only**. Using this tool on networks or systems without explicit permission is illegal and unethical. The authors assume no liability for misuse.

---

**Built for safety, auditability, and clean orchestration.**
