from flask import Blueprint, abort, render_template, session

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import cmd_config_required
from config.json_related import load_commands

bp = Blueprint("admin_remote_commands", __name__, url_prefix="/manage_remote_commands")

@bp.route("/")
@cmd_config_required
def manage_commands():
    userid = session.get('userid')
    user = get_user(userid)
    return render_template("admin/ssh/command_management.html", user=user)

@bp.route("/<int:cmd_id>/params", methods=["GET"])
@cmd_config_required
def manage_params(cmd_id):
    userid = session.get('userid')
    user = get_user(userid)

    # Carrega o comando pra exibir o nome no topo da tela
    commands = load_commands()
    cmd = next((c for c in commands if c["id"] == cmd_id), None)
    if not cmd:
        abort(404, "Comando não encontrado")

    return render_template(
        "admin/ssh/param_management.html",
        user=user,
        cmd_id=cmd_id
    )