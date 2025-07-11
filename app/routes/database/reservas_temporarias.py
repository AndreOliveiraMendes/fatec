import copy
from flask import Blueprint
from flask import flash, session, render_template, request, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from config import PER_PAGE
from app.models import db
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import none_if_empty, parse_time_string, get_user_info, \
    get_query_params, registrar_log_generico_usuario, get_session_or_request, register_return


bp = Blueprint('reservas_temporarias', __name__, url_prefix="/database")

@bp.route("/reservas_temporarias")
@admin_required
def gerenciar_reservas_temporarias():
    redirect_action = None
    flash("Pagina em Desenvolvimento", "warning")
    return redirect(url_for('default.under_dev_page'))