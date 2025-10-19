import json
from copy import deepcopy

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from app.auxiliar.auxiliar_cryptograph import ensure_secret_file, encrypt_field, decrypt_field
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required
from config.mapeamentos import SSH_CRED_FILE
import paramiko
from paramiko.ssh_exception import SSHException, AuthenticationException, NoValidConnectionsError

bp = Blueprint('admin_remote', __name__, url_prefix='/admin')

def load_ssh_credentials():
    if SSH_CRED_FILE.exists():
        with SSH_CRED_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_ssh_credentials(creds):
    SSH_CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SSH_CRED_FILE.open("w", encoding="utf-8") as f:
        json.dump(creds, f, ensure_ascii=False, indent=4)

@bp.route("/gerar_chave")
@admin_required
def gerar_chave():
    key = ensure_secret_file()
    if key:
        flash("✅ Chave de criptografia gerada com sucesso!", "success")
    else:
        flash("⚠️ A chave já estava configurada.", "warning")
    return redirect(url_for("admin.gerenciar_menu"))

@bp.route("/manage_ssh_cred")
@admin_required
def manage_ssh():
    userid = session.get('userid')
    user = get_user_info(userid)
    return render_template("admin/ssh_managment.html", user=user)

@bp.route("/api/ssh/list", methods=["GET"])
@admin_required
def api_ssh_list():
    creds = load_ssh_credentials()
    result = deepcopy(creds)

    for c in result:
        c["has_password"] = bool(c.get("password_ssh"))
        c["has_key"] = bool(c.get("key_ssh"))
        c["has_key_passphrase"] = bool(c.get("key_passphrase"))

        # Remove campos sensíveis antes de enviar
        c.pop("password_ssh", None)
        c.pop("key_ssh", None)
        c.pop("key_passphrase", None)

    return jsonify(result)

@bp.route("/api/ssh/save", methods=["POST"])
@admin_required
def api_ssh_save():
    data = request.get_json() or {}
    data.setdefault("auth_type", "password")
    data.setdefault("key_passphrase", "")
    creds = load_ssh_credentials()

    # 🆔 Normaliza ID
    cred_id = data.get("id")
    if cred_id:
        try:
            cred_id = int(cred_id)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "ID inválido."}), 400
    else:
        cred_id = None

    # ✍️ Atualiza credencial existente
    if cred_id is not None and any(c["id"] == cred_id for c in creds):
        for c in creds:
            if c["id"] == cred_id:
                # Atualiza sempre campos básicos (nome, host, user, porta, tipo)
                for field in ["name_ssh", "host_ssh", "user_ssh", "port_ssh", "auth_type"]:
                    if field in data:
                        c[field] = data[field]

                # 🔐 Atualiza senha/chave/passphrase somente se vier algo não vazio
                if "password_ssh" in data and data["password_ssh"].strip():
                    try:
                        c["password_ssh"] = encrypt_field(data["password_ssh"])
                    except RuntimeError as e:
                        return jsonify({"success": False, "error": str(e)}), 400

                if "key_ssh" in data and data["key_ssh"].strip():
                    try:
                        c["key_ssh"] = encrypt_field(data["key_ssh"])
                    except RuntimeError as e:
                        return jsonify({"success": False, "error": str(e)}), 400

                if "key_passphrase" in data and data["key_passphrase"].strip():
                    try:
                        c["key_passphrase"] = encrypt_field(data["key_passphrase"])
                    except RuntimeError as e:
                        return jsonify({"success": False, "error": str(e)}), 400

                c["id"] = cred_id
                break

    # ➕ Cria nova credencial
    else:
        # Criptografa os campos sensíveis normalmente
        if data.get("password_ssh"):
            try:
                data["password_ssh"] = encrypt_field(data["password_ssh"])
            except RuntimeError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        if data.get("key_ssh"):
            try:
                data["key_ssh"] = encrypt_field(data["key_ssh"])
            except RuntimeError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        if data.get("key_passphrase"):
            try:
                data["key_passphrase"] = encrypt_field(data["key_passphrase"])
            except RuntimeError as e:
                return jsonify({"success": False, "error": str(e)}), 400

        new_id = max([c["id"] for c in creds], default=0) + 1
        data["id"] = new_id
        creds.append(data)
        cred_id = new_id

    save_ssh_credentials(creds)
    return jsonify({"success": True, "id": cred_id})

@bp.route("/api/ssh/delete/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_delete(cred_id):
    creds = load_ssh_credentials()
    new_creds = [c for c in creds if c["id"] != cred_id]
    save_ssh_credentials(new_creds)
    return jsonify({"success": True})

@bp.route("/api/ssh/test/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_test(cred_id):
    creds = load_ssh_credentials()
    cred = next((c for c in creds if c["id"] == cred_id), None)
    if not cred:
        return jsonify({"success": False, "error": "Credencial não encontrada."}), 404

    host = cred.get("host_ssh")
    user = cred.get("user_ssh")
    port = int(cred.get("port_ssh", 22))
    auth_type = cred.get("auth_type", "password")  # default to password if not set

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if auth_type == "key":
            key_enc = cred.get("key_ssh") or ""
            passphrase_enc = cred.get("key_passphrase") or None
            key_str = None
            passphrase = None
            if key_enc:
                try:
                    key_str = decrypt_field(key_enc)
                except Exception as e:
                    return jsonify({"success": False, "error": f"Falha ao descriptografar chave: {e}"})
            if passphrase_enc:
                try:
                    passphrase = decrypt_field(passphrase_enc)
                except Exception as e:
                    return jsonify({"success": False, "error": f"Falha ao descriptografar senha da chave: {e}"})
            if not key_str.strip():
                return jsonify({"success": False, "error": "Nenhuma chave fornecida para autenticação por chave."}), 400

            import io
            key_file = io.StringIO(key_str)
            pkey = paramiko.RSAKey.from_private_key(key_file, password=passphrase)
            client.connect(host, port=port, username=user, pkey=pkey, timeout=5)

        else:  # password auth
            password_enc = cred.get("password_ssh")
            if not password_enc:
                return jsonify({"success": False, "error": "Senha não fornecida para autenticação por senha."}), 400
            try:
                password = decrypt_field(password_enc)
            except Exception as e:
                return jsonify({"success": False, "error": f"Falha ao descriptografar senha: {e}"})
            client.connect(host, port=port, username=user, password=password, timeout=5)

        # Testa um comando simples
        stdin, stdout, stderr = client.exec_command("echo ok")
        output = stdout.read().decode().strip()

        if output == "ok":
            return jsonify({"success": True, "message": "Conexão bem-sucedida ✅"})
        else:
            return jsonify({"success": False, "error": "Conexão estabelecida, mas falha no comando teste."})

    except (AuthenticationException, SSHException, NoValidConnectionsError) as e:
        return jsonify({"success": False, "error": f"Erro de conexão SSH: {e}"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro inesperado: {e}"})
    finally:
        client.close()

@bp.route("/manage_remote_commands")
@admin_required
def manage_commands():
    userid = session.get('userid')
    user = get_user_info(userid)
    return render_template("admin/command_management.html", user=user)

@bp.route("/api/ssh/execute/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_execute(cred_id):
    data = request.get_json() or {}
    command = data.get("command", "").strip()
    stdin_data = data.get("stdin", "")
    if not command:
        return jsonify({"stdout": "", "stderr": "Nenhum comando fornecido."}), 400

    creds = load_ssh_credentials()
    cred = next((c for c in creds if c["id"] == cred_id), None)
    if not cred:
        return jsonify({"stdout": "", "stderr": "Credencial não encontrada."}), 404

    host = cred.get("host_ssh")
    user = cred.get("user_ssh")
    port = int(cred.get("port_ssh", 22))
    auth_type = cred.get("auth_type", "password")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if auth_type == "key":
            import io
            key_str = decrypt_field(cred["key_ssh"])
            passphrase = decrypt_field(cred["key_passphrase"]) if cred.get("key_passphrase") else None
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_str), password=passphrase)
            client.connect(host, port=port, username=user, pkey=pkey, timeout=5)
        else:
            password = decrypt_field(cred["password_ssh"])
            client.connect(host, port=port, username=user, password=password, timeout=5)

        stdin, stdout, stderr = client.exec_command(command)

        # 🔸 Envia dados para o stdin, se houver
        if stdin_data:
            stdin.write(stdin_data)
            stdin.flush()
        stdin.close()

        out = stdout.read().decode()
        err = stderr.read().decode()

        return jsonify({"stdout": out, "stderr": err})

    except Exception as e:
        return jsonify({"stdout": "", "stderr": f"Erro: {e}"})
    finally:
        client.close()
