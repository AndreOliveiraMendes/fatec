from flask import Blueprint, flash, redirect, render_template, session, url_for

from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.security.cryptograph import ensure_secret_file

bp = Blueprint('admin_remote_credential', __name__, url_prefix='/manage_ssh_cred')

@bp.route("/gerar_chave")
@admin_required
def gerar_chave():
    key = ensure_secret_file()
    if key:
        flash("✅ Chave de criptografia gerada com sucesso!", "success")
    else:
        flash("⚠️ A chave já estava configurada.", "warning")
    return redirect(url_for("admin.gerenciar_menu"))

@bp.route("/")
@admin_required
def manage_ssh():
    userid = session.get('userid')
    user = get_user(userid)
    return render_template("admin/ssh/ssh_managment.html", user=user)
