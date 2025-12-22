# 🛸 Dali C 2x2: Advanced Fleet Orchestration Framework

Dali C 2x2 is a professional, job-oriented Command & Control (C2) framework built for secure node orchestration, auditing, and fleet management.

![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![Security](https://img.shields.io/badge/Auth-JWT-orange.svg)
![Realtime](https://img.shields.io/badge/UI-WebSockets-purple.svg)

## 🏗️ Technical Architecture

- **Control Server**: FastAPI backend with **JWT Authentication**, **WebSocket** live-updates, and SQLite persistence.
- **Dali Agent**: A modular, plugin-based execution engine.
- **Plugin System**: Dynamically loads new capabilities (Shell, Sysinfo, Persist) from the `plugins/` directory.

---

## 🚀 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Start the Control Plane

```bash
python -m server.main
```

- **URL**: `http://localhost:8000`
- **Default Credentials**: `admin` / `password123`

### 3. Deploy a Node (Agent)

```bash
# Set server URL and run
export C2_SERVER_URL="http://YOUR_SERVER_IP:8000"
python -m agent.agent
```

---

## 🛠️ Advanced Features

- **Persistent Identity**: Agents store their unique UUID locally in `.agent_id`.
- **Live Orchestration**: WebSocket integration ensures zero-latency feedback on task status.
- **Audit Reports**: Export full execution history to CSV for compliance and review.
- **Windows Persistence**: Built-in plugin to establish Registry-based autorun (HKCU).
- **API Documentation**: Fully interactive Swagger docs available at `/docs` (requires auth).

---

## 📂 Project Structure

```text
c2-framework/
├── server/
│   ├── auth.py         # JWT & Security logic
│   ├── store.py        # Persistence & Orchestration logic
│   ├── templates/      # Secure Dashboard & Login UI
│   └── main.py         # FastAPI Entrypoint & WS Manager
├── agent/
│   ├── plugins/        # Modular task handlers (Drop-in system)
│   ├── executor.py     # Plugin loader & Task router
│   └── agent.py        # Main comms loop
└── shared/             # Pydantic schemas
```

## ⚖️ Legal Disclaimer

This software is for **authorized testing and educational purposes only**. Misuse of this tool is strictly prohibited. The developer assumes no liability for illegal use.
