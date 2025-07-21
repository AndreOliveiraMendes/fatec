from flask import Blueprint, session, render_template, request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import db, Aulas
from app.auxiliar.auxiliar_routes import get_user_info, parse_time_string, registrar_log_generico_usuario
from app.auxiliar.decorators import admin_required

bp = Blueprint('setup', __name__, url_prefix="/database/fast_setup/")

@bp.route("/menu")
@admin_required
def fast_setup_menu():
    userid = session.get('userid')
    username, perm = get_user_info(userid)

    return render_template('database/setup/menu.html', username=username, perm=perm)