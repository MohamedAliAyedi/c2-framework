import sqlite3
import os

db_paths = ["c2_framework.db", "server/c2_framework.db", "../c2_framework.db"]
found = False

for path in db_paths:
    if os.path.exists(path):
        print(f"[*] Found database at: {path}")
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            # Try to add the column
            cursor.execute("ALTER TABLE agents ADD COLUMN agent_type VARCHAR DEFAULT 'binary'")
            conn.commit()
            conn.close()
            print(f"[+] Successfully added 'agent_type' column to {path}")
            found = True
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"[!] Column already exists in {path}")
                found = True
            else:
                print(f"[X] Error migrating {path}: {e}")

if not found:
    print("[!] No database found to migrate. It will be created correctly on next start.")
