import json

from cryptography.fernet import Fernet

from config.mapeamentos import SECRET_PATH, SSH_CRED_PATH


def load_key():
    with open(SECRET_PATH) as f:
        data = json.load(f)
    return data["ENCRYPTION_KEY"].encode()

def encrypt_password(password: str) -> str:
    f = Fernet(load_key())
    return f.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    f = Fernet(load_key())
    return f.decrypt(token.encode()).decode()