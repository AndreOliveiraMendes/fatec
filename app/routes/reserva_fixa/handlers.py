from datetime import date

from flask import (abort, current_app, flash, redirect, render_template,
                   session, url_for)

from app.auxiliar.constant import Permission
from app.dao.external.disponibilidade import get_prioridade
from app.dao.internal.aulas import (get_aulas_ativas_por_semestre,
                                    get_aulas_extras)
from app.dao.internal.locais import get_laboratorios
from app.dao.internal.reservas import check_conflict_reservas_fixas
from app.dao.internal.usuarios import get_user
from app.enums import FinalidadeReservaEnum
from app.extensions import db
from app.models.aulas import Semestres, Turnos
from app.models.locais import Locais
from app.models.usuarios import Usuarios
from app.routes_helper.request import check_local
from app.routes_helper.tables import builder_helper_fixa


def _current_user():
    userid = session.get("userid")
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não autenticado.")
    return userid, user

def _get_semestre_or_403(id_semestre, userid, perm: Permission):
    semestre = db.get_or_404(Semestres, id_semestre)
    _check_semestre(semestre, userid, perm)
    return semestre

def _check_semestre(semestre, userid, perm: Permission):
    if perm.has(Permission.ADMIN):
        return

    today = date.today()

    if not (semestre.data_inicio_reserva <= today <= semestre.data_fim_reserva):
        abort(403, description="Semestre fora do período de reservas.")

    if (today - semestre.data_inicio_reserva).days < semestre.dias_de_prioridade:
        has_priority, prioridade = get_prioridade()
        user = db.get_or_404(Usuarios, userid)

        if has_priority and prioridade and user.pessoa.id_pessoa not in prioridade:
            abort(403, description="Usuário não se enquadra na regra de prioridade.")

def _parse_reserva_key(key: str):
    key = key.removeprefix("reserva[").removesuffix("]") if hasattr(key, "removeprefix") else key[8:-1]
    return tuple(map(int, key.split(",")))

def _has_conflict(semestre, reservas, user):
    dia = semestre.data_inicio
    cache = {}
    visited = set()

    for _, aula in reservas:
        if aula not in cache:
            cache[aula] = check_conflict_reservas_fixas(dia, aula, user.id_pessoa)

        if cache[aula]["conflict"] or aula in visited:
            return True

        visited.add(aula)

    return False

def _build_base_extras(semestre, turno=None, local=None):
    return {
        "semestre": semestre,
        "turno": turno,
        "local": local,
        "day": date.today(),
        "finalidade_reserva": FinalidadeReservaEnum,
        "contador_fixa": session.get("contador_fixa")
    }

def _handle_db_error(e, msg):
    db.session.rollback()
    flash(f"{msg}: {str(getattr(e, 'orig', e))}", "danger")
    current_app.logger.error(f"{msg}: {e}")
    
def _get_lab_geral(id_semestre, id_turno):
    userid, user = _current_user()
    semestre = _get_semestre_or_403(id_semestre, userid, user.perm)

    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    locais = get_laboratorios(user.perm.has(Permission.ADMIN))

    if not aulas or not locais:
        flash("não há recursos disponíveis", "danger")
        return redirect(url_for("default.home"))

    extras = _build_base_extras(semestre, turno)
    extras.update(
        aulas=aulas,
        locais=locais,
        aulas_extras=get_aulas_extras(semestre, turno)
    )

    return render_template("reserva_fixa/geral.html", user=user, **extras)

def _get_lab_especifico(id_semestre, id_turno, id_lab):
    userid, user = _current_user()
    semestre = _get_semestre_or_403(id_semestre, userid, user.perm)

    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    local = db.get_or_404(Locais, id_lab)
    check_local(local, user.perm)

    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    if not aulas:
        flash("não há horários disponíveis", "danger")
        return redirect(url_for("default.home"))

    extras = _build_base_extras(semestre, turno, local)
    builder_helper_fixa(extras, aulas)

    extras.update(
        aulas=aulas,
        locais=get_laboratorios(user.perm.has(Permission.ADMIN)),
        aulas_extras=get_aulas_extras(semestre, turno)
    )

    return render_template("reserva_fixa/especifico.html", user=user, **extras)