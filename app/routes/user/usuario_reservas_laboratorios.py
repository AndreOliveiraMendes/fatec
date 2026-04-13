from datetime import datetime
from typing import Any

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)

from app.auxiliar.constant import Permission
from app.dao.internal.aulas import get_dias_da_semana, get_semestre_by_id, get_semestres
from app.dao.internal.locais import get_laboratorios
from app.dao.internal.usuarios import (get_pessoas, get_user,
                                       get_usuarios_especiais)
from app.decorators.decorators import login_required
from app.enums import FinalidadeReservaEnum
from app.routes.user.handler.handler_laboratorios import \
    get_reservas_laboratorios
from app.routes_helper.request import get_query_params
from config.general import LOCAL_TIMEZONE

bp = Blueprint('usuario_reservas_laboratorios', __name__, url_prefix='/usuario')

@bp.route("/reservas/reservas_fixas")
@login_required
def gerenciar_reserva_fixa():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    semestres = get_semestres()
    if not semestres:
        flash("nenhum semestre definido", "danger")
        return redirect(url_for('default.home'))
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'datetime':today}
    page = int(request.args.get("page", 1))
    args_extras = get_query_params(request, origin="args")
    reservas_fixas = get_reservas_laboratorios(userid, args_extras, page, "fixa")
    extras['reservas_fixas'] = reservas_fixas.items
    for reserva in extras['reservas_fixas']:
        id_semestre = next((s.id_semestre for s in semestres if reserva.id_reserva_semestre == s.id_semestre), None)
        reserva.semestre = get_semestre_by_id(id_semestre) if id_semestre is not None else None
        if not reserva.semestre:
            continue
        reserva.dentro_periodo = reserva.semestre.data_inicio_reserva <= today.date() <= reserva.semestre.data_fim_reserva
    extras['pagination'] = reservas_fixas
    extras['args_extras'] = args_extras
    # for edit and filter
    extras['semestres'] = semestres
    extras['TipoReserva'] = FinalidadeReservaEnum
    extras['TipoReservaList'] = [e.value for e in FinalidadeReservaEnum]
    extras['pessoas'] = get_pessoas()
    extras['pessoasList'] = [{"value":p.id_pessoa, "label": p.nome_pessoa} for p in extras['pessoas']]
    extras['usuarios_especiais'] = get_usuarios_especiais()
    extras['usuarios_especiaisList'] = [{"value":u.id_usuario_especial, "label": u.nome_usuario_especial} for u in extras['usuarios_especiais']]
    extras['laboratorios'] = get_laboratorios(user.perm.has(Permission.ADMIN))
    extras['semanas'] = get_dias_da_semana()
    return render_template("usuario/reservas_laboratorios/reserva_fixa.html", user=user, **extras)

@bp.route("/reserva/reservas_temporarias")
@login_required
def gerenciar_reserva_temporaria():
    userid = session.get('userid')
    user = get_user(userid)
    if not user:
        abort(404, description="Usuário não encontrado.")
    today = datetime.now(LOCAL_TIMEZONE)
    extras: dict[str, Any] = {'datetime':today}
    page = int(request.args.get("page", 1))
    args_extras = get_query_params(request, origin="args")
    reservas_temporarias = get_reservas_laboratorios(userid, args_extras, page, "temporaria")
    extras['reservas_temporarias'] = reservas_temporarias.items
    extras['pagination'] = reservas_temporarias
    extras['args_extras'] = args_extras
    extras['TipoReserva'] = FinalidadeReservaEnum
    extras['TipoReservaList'] = [e.value for e in FinalidadeReservaEnum]
    extras['pessoas'] = get_pessoas()
    extras['pessoasList'] = [{"value":p.id_pessoa, "label": p.nome_pessoa} for p in extras['pessoas']]
    extras['usuarios_especiais'] = get_usuarios_especiais()
    extras['usuarios_especiaisList'] = [{"value":u.id_usuario_especial, "label": u.nome_usuario_especial} for u in extras['usuarios_especiais']]
    extras['laboratorios'] = get_laboratorios(user.perm.has(Permission.ADMIN))
    extras['semanas'] = get_dias_da_semana()
    return render_template("usuario/reservas_laboratorios/reserva_temporaria.html", user=user, **extras)
