from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, session

from app.auxiliar.auxiliar_api import run_remote_command
from app.auxiliar.auxiliar_routes import get_user
from app.auxiliar.decorators import admin_required, cmd_config_required
from config.json_related import load_commands, save_commands

bp = Blueprint('api_commands', __name__, url_prefix='/api/commands')

@bp.route("/list", methods=["GET"])
@admin_required
def api_list_commands():
    return jsonify(load_commands())

@bp.route("/save", methods=["POST"])
@cmd_config_required
def api_save_command():
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

@bp.route("/delete/<int:cmd_id>", methods=["DELETE"])
@cmd_config_required
def api_delete_command(cmd_id):
    commands = load_commands()
    new_commands = [c for c in commands if c["id"] != cmd_id]
    if len(new_commands) == len(commands):
        return jsonify({"success": False, "error": "Comando não encontrado."}), 404

    save_commands(new_commands)
    return jsonify({"success": True})

@bp.route("/<int:cmd_id>", methods=["GET"])
@admin_required
def api_get_command(cmd_id):
    commands = load_commands()
    cmd = next((c for c in commands if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"error": "Comando não encontrado"}), 404
    return jsonify(cmd)

@bp.route("/<int:cmd_id>/params", methods=["POST"])
@cmd_config_required
def api_save_param(cmd_id):
    data = request.get_json() or {}
    commands = load_commands()

    cmd = next((c for c in commands if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"success": False, "error": "Comando não encontrado"}), 404

    params = cmd.setdefault("params", [])
    param_id = data.get("id")

    # Validação simples
    if not data.get("name"):
        return jsonify({"success": False, "error": "Campo 'name' é obrigatório."}), 400

    # Atualizar
    if param_id is not None:
        try:
            param_id = int(param_id)
            data["id"] = param_id
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "ID inválido"}), 400

        updated = False
        for p in params:
            if p["id"] == param_id:
                p.update(data)
                updated = True
                break
        if not updated:
            return jsonify({"success": False, "error": "Parâmetro não encontrado"}), 404
    else:
        # Criar novo
        new_id = max((p["id"] for p in params), default=0) + 1
        data["id"] = new_id
        params.append(data)
        param_id = new_id

    save_commands(commands)
    return jsonify({"success": True, "id": param_id})

@bp.route("/<int:cmd_id>/params/<int:param_id>", methods=["DELETE"])
@cmd_config_required
def api_delete_param(cmd_id, param_id):
    commands = load_commands()
    cmd = next((c for c in commands if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"success": False, "error": "Comando não encontrado"}), 404

    params = cmd.get("params", [])
    new_params = [p for p in params if p["id"] != param_id]

    if len(new_params) == len(params):
        return jsonify({"success": False, "error": "Parâmetro não encontrado"}), 404

    cmd["params"] = new_params
    save_commands(commands)

    return jsonify({"success": True})

@bp.route("/run_command", methods=["POST"])
@admin_required
def api_run_command():
    
    data = request.get_json(force=True)
    cmd_id = data.get("cmd_id")
    lab_id = data.get("lab_id")
    parametros = data.get("parametros", {})

    # 1️⃣ — Identifica o usuário atual (pra log)
    userid = session.get("userid")
    user = get_user(userid)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado."}), 404
    

    # 2️⃣ — Carrega o comando
    comandos = load_commands()
    cmd = next((c for c in comandos if c["id"] == cmd_id), None)
    if not cmd:
        return jsonify({"success": False, "error": "Comando não encontrado."}), 404

    # 3️⃣ — Monta o comando final
    try:
        comando_final = cmd["template"].format(**parametros)
    except KeyError as e:
        return jsonify({"success": False, "error": f"Parâmetro ausente: {e.args[0]}"}), 400

    # 4️⃣ — Loga execução
    current_app.logger.info(
        f"[COMANDO] User={user.pessoa.nome_pessoa} (ID {user.id_usuario}) | "
        f"Cmd='{cmd['name']}' | Lab={lab_id or '-'} | "
        f"Template='{cmd['template']}' | Exec='{comando_final}' | "
        f"Hora={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # 5️⃣ — Executa via SSH
    resultado = run_remote_command(cmd["cred_ssh"], comando_final)

    # 6️⃣ — Retorna JSON pra o modal no front
    return jsonify({
        "success": resultado["success"],
        "stdout": resultado.get("stdout", ""),
        "stderr": resultado.get("stderr", ""),
        "exit_code": resultado.get("exit_code"),
        "command": comando_final,
        "executed_by": user.pessoa.nome_pessoa,
        "lab_id": lab_id
    })