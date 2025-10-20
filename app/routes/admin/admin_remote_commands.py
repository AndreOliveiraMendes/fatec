import paramiko
from flask import Blueprint, jsonify, render_template, request, session

from app.auxiliar.auxiliar_cryptograph import decrypt_field
from app.auxiliar.auxiliar_routes import get_user_info
from app.auxiliar.decorators import admin_required
from config.json_related import (load_commands, load_ssh_credentials,
                                 save_commands)

bp = Blueprint("admin_remote_commands", __name__, url_prefix="/api/commands")

# 📄 Listar comandos
@bp.route("/list", methods=["GET"])
@admin_required
def list_commands():
    return jsonify(load_commands())

# 💾 Salvar (adicionar ou editar)
@bp.route("/save", methods=["POST"])
@admin_required
def save_command():
    data = request.get_json() or {}
    commands = load_commands()

    # Validação simples
    if not data.get("name") or not data.get("template") or not data.get("cred_ssh"):
        return jsonify({"success": False, "error": "Campos obrigatórios faltando."}), 400


    cmd_id = data.get("id")
    if cmd_id:
        try:
            cmd_id = int(cmd_id)
            data["id"] = cmd_id
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "ID inválido."}), 400

    if cmd_id:
        # Atualiza existente
        updated = False
        for c in commands:
            if c["id"] == cmd_id:
                c.update(data)
                updated = True
                break
        if not updated:
            return jsonify({"success": False, "error": "Comando não encontrado."}), 404
    else:
        # Cria novo
        new_id = max([c["id"] for c in commands], default=0) + 1
        data["id"] = new_id
        data.setdefault("params", [])
        data.setdefault("active", True)
        commands.append(data)
        cmd_id = new_id

    save_commands(commands)
    return jsonify({"success": True, "id": cmd_id})

# 🗑️ Deletar comando
@bp.route("/delete/<int:cmd_id>", methods=["DELETE"])
@admin_required
def delete_command(cmd_id):
    commands = load_commands()
    new_commands = [c for c in commands if c["id"] != cmd_id]
    if len(new_commands) == len(commands):
        return jsonify({"success": False, "error": "Comando não encontrado."}), 404

    save_commands(new_commands)
    return jsonify({"success": True})

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

@bp.route("/manage_remote_commands")
@admin_required
def manage_commands():
    userid = session.get('userid')
    user = get_user_info(userid)
    return render_template("admin/command_management.html", user=user)