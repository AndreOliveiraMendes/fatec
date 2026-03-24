from datetime import datetime
from typing import Any

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy import select

from app.dao.internal.aulas import get_dias_da_semana, get_semestres
from app.dao.internal.locais import get_laboratorios
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.aulas import Aulas, Dias_da_Semana
from app.routes.admin.handlers.handler_admin import get_reservas, make_params
from app.routes_helper.ui import get_log_summary
from app.security.cryptograph import load_key
from config.database_views import SECOES
from config.general import LOCAL_TIMEZONE

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route("/")
@admin_required
def gerenciar_menu():
    userid = session.get('userid')
    user = get_user(userid)
    key = load_key()
    error_count, last_lines = get_log_summary()
    return render_template("admin/painel/admin.html", user=user,
        secoes=SECOES, key=key, error_count=error_count, last_lines=last_lines)

@bp.route("/times")
@admin_required
def control_times():
    userid = session.get('userid')
    user = get_user(userid)
    hoje = datetime.now(LOCAL_TIMEZONE).date()
    extras: dict[str, Any] = {'hoje': hoje}
    extras['dias_da_semana'] = db.session.execute(
        select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    ).scalars().all()
    extras['horarios_base'] = db.session.execute(
        select(Aulas).order_by(Aulas.horario_inicio, Aulas.horario_fim)
    ).scalars().all()
    return render_template("admin/times.html", user=user, **extras)

@bp.route("/observações")
@admin_required
def menu_reservas():
    userid = session.get('userid')
    user = get_user(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'datetime':today}
    return render_template("admin/observacoes/menu_reserva.html", user=user, **extras)

@bp.route("/observações/reservas_fixas")
@admin_required
def get_observações_fixa():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    semestres = get_semestres()
    if not semestres:
        flash("nenhum semestre definido", "danger")
        return redirect(url_for('default.home'))
    page = int(request.args.get("page", 1))
    args_extras = make_params(request)
    reservas_fixas = get_reservas(args_extras, page, "fixa")
    extras = {}
    # filtro
    extras['semestres'] = semestres
    extras['laboratorios'] = get_laboratorios(True)
    extras['semanas'] = get_dias_da_semana()
    # reserva
    extras['reservas_fixas'] = reservas_fixas.items
    extras['pagination'] = reservas_fixas
    # pra conservar os parametros
    extras['args_extras'] = args_extras
    return render_template("admin/observacoes/observações_fixa.html", user=user, **extras)

@bp.route('/observações/reservas_temporarias')
@admin_required
def get_observações_temporaria():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    semestres = get_semestres()
    if not semestres:
        flash("nenhum semestre definido", "danger")
        return redirect(url_for('default.home'))
    page = int(request.args.get("page", 1))
    args_extras = make_params(request)
    reservas_temporaria = get_reservas(args_extras, page, "temporaria")
    extras = {}
    # filtro
    extras['laboratorios'] = get_laboratorios(True)
    extras['semanas'] = get_dias_da_semana()
    # reserva
    extras['reservas_temporarias'] = reservas_temporaria.items
    extras['pagination'] = reservas_temporaria
    # pra conservar os parametros
    extras['args_extras'] = args_extras
    return render_template("admin/observacoes/observações_temporaria.html", user=user, **extras)