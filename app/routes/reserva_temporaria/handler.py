from datetime import date
from typing import List

from flask import (abort, current_app, flash, redirect, render_template,
                   session, url_for)

from app.auxiliar.constant import Permission
from app.auxiliar.dates import time_range
from app.auxiliar.general import none_if_empty
from app.dao.internal.aulas import get_aulas_ativas_por_lista_de_dias
from app.dao.internal.locais import get_laboratorios
from app.dao.internal.usuarios import (get_pessoas, get_user,
                                       get_usuarios_especiais)
from app.enums import FinalidadeReservaEnum, TipoAulaEnum
from app.extensions import db
from app.models.aulas import Turnos
from app.models.locais import Locais
from app.routes_helper.request import check_local
from app.routes_helper.tables import builder_helper_temporaria
from config.json_related import carregar_config_geral


def agrupar_dias(dias: List[date]) -> List[List[date]]:
    if not dias:
        return []

    dias = sorted(dias)
    grupos = [[dias[0]]]

    for dia in dias[1:]:
        if (dia - grupos[-1][-1]).days <= 7:
            grupos[-1].append(dia)
        else:
            grupos.append([dia])

    return grupos

def _base_context(inicio, fim, turno):
    return {
        "inicio": inicio,
        "fim": fim,
        "turno": turno,
        "fake_data": date(2000, 1, 1),
        "finalidade_reserva": FinalidadeReservaEnum,
        "responsavel": get_pessoas(),
        "responsavel_especial": get_usuarios_especiais(),
        "contador_temporaria": session.get("contador_temporaria"),
        "cfg": carregar_config_geral()
    }

def _obter_tipo_horario():
    valor = none_if_empty(session.get("tipo"))
    try:
        return TipoAulaEnum(valor)
    except ValueError as e:
        current_app.logger.error(f"error:{e}")
        abort(400, description="tipo de horario invalido")

def get_lab_geral(inicio, fim, id_turno):
    user = get_user(session.get("userid"))
    if not user:
        abort(404, description="usuario não encontrado")

    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    tipo = _obter_tipo_horario()

    locais = get_laboratorios(user.perm.has(Permission.ADMIN))
    dias = [(dia, turno) for dia in time_range(inicio, fim)]
    aulas = get_aulas_ativas_por_lista_de_dias(dias, tipo)

    if not aulas or not locais:
        if not aulas:
            flash("não há horarios disponiveis nesse turno", "danger")
        if not locais:
            flash("não há local disponivel para reserva", "danger")
        return redirect(url_for("default.home"))

    ctx = _base_context(inicio, fim, turno)
    ctx.update({"locais": locais, "aulas": aulas})

    return render_template(
        "reserva_temporaria/geral.html",
        user=user,
        **ctx
    )

def get_lab_especifico(inicio, fim, id_turno, id_lab):
    user = get_user(session.get("userid"))
    if not user:
        abort(404, description="usuario não encontrado")

    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    tipo = _obter_tipo_horario()

    local = db.get_or_404(Locais, id_lab)
    check_local(local, user.perm)

    dias = [(dia, turno) for dia in time_range(inicio, fim)]
    aulas = get_aulas_ativas_por_lista_de_dias(dias, tipo)

    if not aulas:
        flash("não há horarios disponiveis nesse turno", "danger")
        return redirect(url_for("default.home"))

    ctx = _base_context(inicio, fim, turno)
    builder_helper_temporaria(ctx, aulas)

    ctx.update({
        "local": local,
        "aulas": aulas,
        "locais": get_laboratorios(user.perm.has(Permission.ADMIN)),
        "day": date.today()
    })

    return render_template(
        "reserva_temporaria/especifico.html",
        user=user,
        **ctx
    )