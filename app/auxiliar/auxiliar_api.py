import shlex

from app.security.auxiliar_cryptograph import decrypt_field
from config.json_related import load_ssh_credentials


# helper functions for command API routes
def wrap_command(command: str, full_path: bool) -> str:
    if full_path:
        return f"bash -lc {shlex.quote(command)}"
    return command

def run_remote_command(cred_ssh, command):
    """Executa um comando remoto via SSH e retorna stdout/stderr separados."""
    import io

    import paramiko

    creds = load_ssh_credentials()
    cred = next((c for c in creds if c["id"] == int(cred_ssh)), None)
    if not cred:
        return {"success": False, "error": "Credencial SSH não encontrada."}

    host = cred.get("host_ssh")
    user = cred.get("user_ssh")
    port = int(cred.get("port_ssh", 22))
    auth_type = cred.get("auth_type", "password")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if auth_type == "key":
            key_str = decrypt_field(cred["key_ssh"])
            passphrase = decrypt_field(cred["key_passphrase"]) if cred.get("key_passphrase") else None
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_str), password=passphrase)
            client.connect(host, port=port, username=user, pkey=pkey, timeout=10)
        else:
            password = decrypt_field(cred["password_ssh"])
            client.connect(host, port=port, username=user, password=password, timeout=10)

        stdin, stdout, stderr = client.exec_command(command)

        out = stdout.read().decode(errors="ignore").strip()
        err = stderr.read().decode(errors="ignore").strip()
        exit_code = stdout.channel.recv_exit_status()

        return {
            "success": True,
            "stdout": out,
            "stderr": err,
            "exit_code": exit_code
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1
        }
    finally:
        client.close()
