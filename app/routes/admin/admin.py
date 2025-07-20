from flask import Blueprint, session, render_template
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import get_user_info
from config.database_views import SECOES

bp = Blueprint('admin', __name__)

@bp.route("/admin")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("admin/admin.html", username=username, perm=perm, secoes=SECOES)