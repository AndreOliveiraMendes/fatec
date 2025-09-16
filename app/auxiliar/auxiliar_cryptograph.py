import json
import os

from cryptography.fernet import Fernet

from config.mapeamentos import SECRET_PATH, SSH_CRED_PATH


def ensure_secret_file(path=SECRET_PATH):
    if os.path.exists(path):
        return None  # já existe
    os.makedirs(os.path.dirname(path), exist_ok=True)
    key = Fernet.generate_key().decode()
    with open(path, "w") as f:
        json.dump({"ENCRYPTION_KEY": key}, f, indent=4)
    try:
        os.chmod(path, 0o600)  # Unix only
    except Exception:
        pass
    return key

def load_key():
    try:
        with open(SECRET_PATH) as f:
            data = json.load(f)
        return data["ENCRYPTION_KEY"].encode()
    except FileNotFoundError:
        return None

def encrypt_password(password: str) -> str:
    f = Fernet(load_key())
    return f.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    f = Fernet(load_key())
    return f.decrypt(token.encode()).decode()