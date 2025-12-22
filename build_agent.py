import PyInstaller.__main__
import os
import shutil

# Get absolute path of the project root
root = os.path.dirname(os.path.abspath(__file__))

# Define paths
agent_path = os.path.join(root, "agent", "agent.py")
shared_path = os.path.join(root, "shared")

print(f"[*] Building agent from {agent_path}")

PyInstaller.__main__.run([
    agent_path,
    '--onefile',
    '--noconsole',
    '--name=c2_agent',
    f'--add-data={shared_path}{os.pathsep}shared',
    '--clean',
    '--log-level=INFO'
])

print("[+] Build complete. Check the 'dist' folder for c2_agent.exe")
