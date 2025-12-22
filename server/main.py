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
from datetime import datetime, timedelta
from .auth import create_access_token, get_current_user, verify_password, get_password_hash
from fastapi.security import OAuth2PasswordRequestForm

# Add the parent directory to sys.path to allow importing from 'shared'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import Task
from .store import DataStore

app = FastAPI(title="Dali C 2x2")
store = DataStore()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

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
async def register_agent(agent_id: str, info: dict = None, version: str = "1.0.0"):
    store.register_agent(agent_id, info=info, version=version)
    await manager.broadcast({"event": "agent_registered", "agent_id": agent_id})
    return {"status": "registered", "agent_id": agent_id}

@app.get("/tasks/{agent_id}", response_model=List[Task])
async def get_tasks(agent_id: str):
    tasks = store.get_pending_tasks(agent_id)
    return [Task(id=t.id, type=t.type, payload=t.payload, expires_at=t.expires_at) for t in tasks]

@app.post("/tasks/{agent_id}/results")
async def submit_result(agent_id: str, task_id: str, result: dict):
    store.update_task_result(task_id, result)
    await manager.broadcast({"event": "task_updated", "agent_id": agent_id, "task_id": task_id})
    return {"status": "received"}

@app.post("/operator/tasks")
async def create_task(agent_id: str, task_type: str, command: str, expires_minutes: int = 60, user: str = Depends(get_current_user)):
    from datetime import timedelta
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    task_id = store.add_task(agent_id, task_type, {"command": command}, expires_at)
    await manager.broadcast({"event": "task_created", "agent_id": agent_id, "task_id": task_id})
    return {"status": "task_created", "task_id": task_id}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str, user: str = Depends(get_current_user)):
    success = store.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    await manager.broadcast({"event": "agent_deleted", "agent_id": agent_id})
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
