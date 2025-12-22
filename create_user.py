import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.store import DataStore
from server.auth import get_password_hash

def main():
    if len(sys.argv) < 3:
        print("Usage: python create_user.py <username> <password>")
        return

    username = sys.argv[1]
    password = sys.argv[2]

    store = DataStore()
    
    # Check if user already exists
    if store.get_user(username):
        print(f"[!] Error: User '{username}' already exists.")
        return

    hashed_pw = get_password_hash(password)
    store.create_user(username, hashed_pw)
    
    print(f"[+] Successfully created operator: {username}")

if __name__ == "__main__":
    main()
