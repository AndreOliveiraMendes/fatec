import uuid
from copy import deepcopy

import paramiko
from flask import Blueprint, abort, current_app, jsonify, request, session
from paramiko.ssh_exception import (AuthenticationException,
                                    NoValidConnectionsError, SSHException)

from app.auxiliar.api import wrap_command
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.security.cryptograph import decrypt_field, encrypt_field
from config.json_related import load_ssh_credentials, save_ssh_credentials

bp = Blueprint('api_ssh', __name__, url_prefix='/api/ssh')

@bp.route("/list", methods=["GET"])
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

@bp.route("/save", methods=["POST"])
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

@bp.route("/delete/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_delete(cred_id):
    creds = load_ssh_credentials()
    new_creds = [c for c in creds if c["id"] != cred_id]
    save_ssh_credentials(new_creds)
    return jsonify({"success": True})

@bp.route("/test/<int:cred_id>", methods=["POST"])
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
            if not (key_str and key_str.strip()):
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

@bp.route("/execute/<int:cred_id>", methods=["POST"])
@admin_required
def api_ssh_execute(cred_id):
    current_user = get_user(session.get('userid'))
    if not current_user:
        abort(403, description="usuario não encontrado")

    exec_id = uuid.uuid4().hex[:8]

    data = request.get_json() or {}
    command = data.get("command", "").strip()
    stdin_data = data.get("stdin", "")
    full_path = bool(data.get("full_path", True))

    # -------- validação comando --------
    if not command:
        current_app.logger.warning(
            "[SSH#%s] Comando vazio | User=%s",
            exec_id,
            current_user.id_usuario
        )
        return jsonify({"stdout": "", "stderr": "Nenhum comando fornecido."}), 400

    # -------- busca credencial --------
    creds = load_ssh_credentials()
    cred = next((c for c in creds if c["id"] == cred_id), None)

    if not cred:
        current_app.logger.warning(
            "[SSH#%s] Credencial não encontrada | CredID=%s | User=%s",
            exec_id,
            cred_id,
            current_user.id_usuario
        )
        return jsonify({"stdout": "", "stderr": "Credencial não encontrada."}), 404

    host = cred.get("host_ssh")
    user = cred.get("user_ssh")
    port = int(cred.get("port_ssh", 22))
    auth_type = cred.get("auth_type", "password")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    wrapped_command = wrap_command(command, full_path)

    # -------- log técnico (timeline) --------
    current_app.logger.info(
        "[SSH#%s] START User=%s Host=%s",
        exec_id,
        current_user.id_usuario,
        host
    )

    # -------- log auditoria --------
    current_app.cmd_logger.info(
        "[CMD#%s] User=%s (ID %s) | Host=%s | Port=%s | Auth=%s | Cmd=%r | Wrapped=%r",
        exec_id,
        getattr(current_user.pessoa, "nome_pessoa", "-"),
        current_user.id_usuario,
        host,
        port,
        auth_type,
        command,
        wrapped_command
    )

    try:
        # -------- autenticação --------
        if auth_type == "key":
            import io
            key_str = decrypt_field(cred["key_ssh"])
            passphrase = decrypt_field(cred["key_passphrase"]) if cred.get("key_passphrase") else None
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_str), password=passphrase)
            client.connect(host, port=port, username=user, pkey=pkey, timeout=5)
        else:
            password = decrypt_field(cred["password_ssh"])
            client.connect(host, port=port, username=user, password=password, timeout=5)

        # -------- execução --------
        stdin, stdout, stderr = client.exec_command(wrapped_command)

        if stdin_data:
            stdin.write(stdin_data)
            stdin.flush()
        stdin.close()

        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        exit_code = stdout.channel.recv_exit_status()

        # -------- log técnico --------
        current_app.logger.info(
            "[SSH#%s] END Exit=%s",
            exec_id,
            exit_code
        )

        # -------- log auditoria --------
        current_app.cmd_logger.info(
            "[RES#%s] Exit=%s | Stdout=%r | Stderr=%r",
            exec_id,
            exit_code,
            out,
            err
        )

        return jsonify({"stdout": out, "stderr": err})

    except Exception as e:

        # técnico
        current_app.logger.exception(
            "[SSH#%s] ERROR Host=%s",
            exec_id,
            host
        )

        # auditoria
        current_app.cmd_logger.error(
            "[ERR#%s] Host=%s | Cmd=%r | Error=%s",
            exec_id,
            host,
            wrapped_command,
            str(e)
        )

        return jsonify({"stdout": "", "stderr": f"Erro: {e}"})

    finally:
        client.close()