from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List
import uvicorn
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to allow importing from 'shared'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import Task
from .store import DataStore

app = FastAPI(title="C2 Framework")
store = DataStore()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="server/static"), name="static")
templates = Jinja2Templates(directory="server/templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/agents")
async def get_all_agents():
    agents = store.get_all_agents()
    return [{
        "id": a.id, 
        "status": a.status,
        "version": a.version,
        "last_seen": a.last_seen, 
        "info": a.info
    } for a in agents]

@app.get("/api/tasks")
async def get_all_tasks():
    tasks = store.get_all_tasks()
    return tasks

@app.get("/api/stats")
async def get_stats():
    return store.get_stats()

@app.get("/api/tasks/{agent_id}")
async def get_agent_tasks_history(agent_id: str):
    tasks = store.get_agent_tasks(agent_id)
    return tasks

@app.post("/register")
async def register_agent(agent_id: str, info: dict = None, version: str = "1.0.0"):
    store.register_agent(agent_id, info=info, version=version)
    return {"status": "registered", "agent_id": agent_id}

@app.get("/tasks/{agent_id}", response_model=List[Task])
async def get_tasks(agent_id: str):
    tasks = store.get_pending_tasks(agent_id)
    return [Task(id=t.id, type=t.type, payload=t.payload, expires_at=t.expires_at) for t in tasks]

@app.post("/tasks/{agent_id}/results")
async def submit_result(agent_id: str, task_id: str, result: dict):
    store.update_task_result(task_id, result)
    return {"status": "received"}

@app.post("/operator/tasks")
async def create_task(agent_id: str, task_type: str, command: str, expires_minutes: int = 60):
    from datetime import timedelta
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    task_id = store.add_task(agent_id, task_type, {"command": command}, expires_at)
    return {"status": "task_created", "task_id": task_id}

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
