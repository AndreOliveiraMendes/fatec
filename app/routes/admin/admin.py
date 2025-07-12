from flask import Blueprint, session, render_template, request, redirect, url_for
from app.models import db, Reservas_Fixas, Usuarios, Permissoes, Laboratorios, Aulas
from app.auxiliar.decorators import login_required, admin_required
from app.auxiliar.auxiliar_routes import get_user_info
from config.database_views import SECOES

bp = Blueprint('admin', __name__)

@bp.route("/admin")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("admin/admin.html", username=username, perm=perm, secoes=SECOES)