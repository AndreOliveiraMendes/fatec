from flask import Blueprint, session, render_template, request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import db, Turnos
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string, registrar_log_generico_usuario, \
    none_if_empty
from app.auxiliar.decorators import admin_required
from config.database_views import SETUP_HEAD

bp = Blueprint('setup_turnos', __name__, url_prefix="/database/fast_setup/")

@bp.route("/turnos", methods=['GET', 'POST'])
@admin_required
def fast_setup_turnos():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    stage = int(request.form.get('stage', request.args.get('stage', 0)))
    extras = {'extras':SETUP_HEAD}

    return render_template('database/setup/turnos.html',
        username=username, perm=perm, stage=stage, **extras)