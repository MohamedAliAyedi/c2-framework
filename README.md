# 🛸 Dali C2 😈: Professional Fleet Orchestration Framework

![Dali Dashboard Banner](images/dashboard.png)

Dali C2 ❤️ is a high-performance, job-oriented Command & Control (C2) framework designed for secure node orchestration, auditing, and real-time surveillance. It features a modern, glassmorphic Control Plane and a modular, plugin-based agent architecture with military-grade encryption and identity spoofing.

---

## 🏗️ Technical Architecture

Dali C2 ❤️ is built on a distributed architecture that separates the **Control Plane** (Server) from the **Managed Nodes** (Agents).

- **Control Plane (FastAPI & WebSockets)**:
  - **JWT Authentication**: Secure operator access with hashed password storage.
  - **AES-CBC Encryption**: 128-bit encrypted communication for all agent-server traffic.
  - **Real-Time Engine**: WebSocket broadcasting for instant job updates and live telemetry.
  - **Glassmorphic UI**: Premium dashboard designed for dark-mode operations.
- **Managed Node (Dali Agent)**:
  - **Plugin System**: Dynamic loading of `screenshot`, `camera`, `keylogger`, and `shell` modules.
  - **Identity Spoofing**: Mimics browser, Windows Update, or custom User-Agents to bypass network filtering.
  - **Persistent Hardware Logic**: Unique node identification linked to hardware profiles.

---

## 🛡️ Security & Ops Features

![Dali Login Portal](images/login.png)

### 🔐 Encrypted Comms

Every packet sent between the agent and the server is encrypted using **AES-CBC (128-bit)** with a shared secret key configured in your `.env`. This prevents MITM (Man-in-the-middle) inspection of your payloads and exfiltrated data.

### 🎭 Identity Spoofing

The agent can hide in plain sight by masquerading as legitimate software.

- `browser`: Mimics Chrome on Windows.
- `updater`: Mimics Windows Delivery Optimization.
- `legit_service`: Mimics the Windows Update Agent.

### 📁 Pro File Management

- **GUI Upload**: Select files directly from your computer via a file picker; the dashboard handles the base64 encoding and encrypted deployment.
- **Direct Save Download**: Exfiltrated files are detected by the dashboard and presented as a "Save File" button for direct browser download.

---

## 🎮 Specialized Forensic Tooling

Dali C2 includes dedicated live-interaction modals for high-stakes telemetry:

- **📟 Live Terminal**: A full pseudo-shell with command history (Up/Down arrows) and real-time results streaming.
- **⌨️ HID Intercept**: A professional keylogger with a live data stream modal. Deploy, Monitor, and Terminate listeners in real-time.
- **🖥️ Desktop Stream**: Synchronize with the remote desktop. View the target's screen live at 2-second intervals.
- **📷 Camera Stream**: Remote webcam access with optimized JPEG compression for low-bandwidth environments.

---

## 🚀 Quick Start

### 1. Requirements

Install the core forensic and web dependencies:

```bash
pip install -r requirements.txt
```

_Note: Includes fastapi, uvicorn, pycryptodome, pynput, mss, and opencv-python._

### 2. Configuration (`.env`)

Create your `.env` file based on the example:

```bash
C2_AES_KEY=DaliSecureC2Key_   # MUST BE 16 CHars
AGENT_IDENTITY=browser       # Choose: browser, updater, etc.
```

### 3. Deployment

- **Control Plane**: `python -m server.main`
- **Managed Node**: `python agent/agent.py`

---

## 🛠️ Command Profiles

| Profile           | Vector       | Description                                 |
| :---------------- | :----------- | :------------------------------------------ |
| **Telemetry**     | `sysinfo`    | Gathers hardware, OS, and user details.     |
| **Shell**         | `shell`      | Standard interactive system command.        |
| **Direct Exec**   | `exec`       | Direct binary execution (bypasses cmd.exe). |
| **HID Intercept** | `keylogger`  | Hardware-level keystroke interception.      |
| **Visual Sync**   | `screenshot` | Real-time primary monitor capture.          |
| **Camera Sync**   | `camera`     | Remote webcam frame exfiltration.           |
| **Exfiltrate**    | `download`   | Binary-safe file retrieval.                 |
| **Deploy**        | `upload`     | Artifact deployment to remote disk.         |

---

## ⚖️ Legal Disclaimer

This software is intended for **authorized security testing and educational purposes only**. Using this tool on networks or systems without explicit permission is illegal. The developer assume no liability for misuse or damage.

**Dali C2 | The Modern Standard for Fleet Intelligence.**
