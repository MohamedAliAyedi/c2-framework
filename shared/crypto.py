import base64
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from dotenv import load_dotenv

load_dotenv()

AES_KEY = os.getenv("C2_AES_KEY", "DaliSecureC2Key_").encode('utf-8')

def encrypt_payload(data: dict) -> str:
    """Encrypts a dictionary into a base64 encoded AES-CBC string."""
    try:
        json_data = json.dumps(data).encode('utf-8')
        # Generate a random 16-byte IV
        iv = os.urandom(16)
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(json_data, AES.block_size))
        # Return IV + Encrypted Data as base64
        return base64.b64encode(iv + encrypted).decode('utf-8')
    except Exception as e:
        print(f"[!] Encryption error: {e}")
        return ""

def decrypt_payload(encrypted_b64: str) -> dict:
    """Decrypts a base64 AES-CBC string into a dictionary."""
    try:
        raw_data = base64.b64decode(encrypted_b64)
        iv = raw_data[:16]
        encrypted_content = raw_data[16:]
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_content), AES.block_size)
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        print(f"[!] Decryption error: {e}")
        return {"status": "error", "error": "Decryption failed"}
