from flask import Blueprint, render_template, session

from app.dao.internal.usuarios import get_user

bp = Blueprint("admin_archive", __name__, url_prefix='/admin/archive')

@bp.route("/menu")
def menu():
    user = get_user(session.get('userid'))

    return render_template("admin/archive/menu.html", user=user)