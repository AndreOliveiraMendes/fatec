from datetime import date
from urllib.parse import urlparse

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from markupsafe import Markup
from sqlalchemy import select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_api import check_conflict_reservas_fixas
from app.auxiliar.auxiliar_routes import (builder_helper_fixa, check_local,
                                          get_user, none_if_empty,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import (get_aulas_ativas_por_semestre, get_aulas_extras,
                              get_laboratorios, get_pessoas,
                              get_usuarios_especiais)
from app.auxiliar.decorators import reserva_fixa_required
from app.auxiliar.external_dao import get_prioridade
from app.models import (FinalidadeReservaEnum, Locais, Permissoes,
                        Reservas_Fixas, Semestres, Turnos, Usuarios, db)

# ========= BLUEPRINT =========
bp = Blueprint('reservas_semanais', __name__, url_prefix="/reserva_fixa")


# ========= HELPERS =========

def _current_user():
    userid = session.get("userid")
    user = get_user(userid)
    if not user:
        abort(403, description="Usuário não autenticado.")
    return userid, user


def _get_semestre_or_403(id_semestre, userid, perm):
    semestre = db.get_or_404(Semestres, id_semestre)
    _check_semestre(semestre, userid, perm)
    return semestre


def _check_semestre(semestre, userid, perm):
    if perm & PERM_ADMIN:
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
        "responsavel": get_pessoas(),
        "responsavel_especial": get_usuarios_especiais(),
        "contador_fixa": session.get("contador_fixa")
    }


def _handle_db_error(e, msg):
    db.session.rollback()
    flash(f"{msg}: {str(getattr(e, 'orig', e))}", "danger")
    current_app.logger.error(f"{msg}: {e}")


# ========= REQUEST HOOK =========

@bp.before_request
def return_counter():
    if request.endpoint != "reservas_semanais.get_lab":
        session.pop("contador_fixa", None)
        return

    path = urlparse(request.headers.get("Referer", "")).path
    parts = path.strip("/").split("/")

    dentro = (
        len(parts) in (5, 6, 7)
        and parts[:2] == ["reserva_fixa", "semestre"]
        and parts[2].isdigit()
        and parts[3] == "turno"
    )

    session["contador_fixa"] = session.get("contador_fixa", 0) + 1 if dentro else 1


# ========= ROUTES =========

@bp.route("/")
@reserva_fixa_required
def main_page():
    userid, user = _current_user()

    semestres = db.session.execute(
        select(Semestres).order_by(Semestres.data_inicio)
    ).scalars().all()

    if not semestres:
        flash("cadastre ao menos um semestre", "danger")
        return redirect(url_for("default.home"))

    today = date.today()

    for s in semestres:
        state = (
            "success" if today < s.data_inicio
            else "primary" if today <= s.data_fim
            else "default"
        )

        icon = ""
        if not (s.data_inicio_reserva <= today <= s.data_fim_reserva):
            if not (user and user.perm & PERM_ADMIN):
                state += " disabled"
            icon = Markup("<span class='glyphicon glyphicon-lock'></span>")
        elif (today - s.data_inicio_reserva).days < s.dias_de_prioridade:
            icon = Markup("<span class='glyphicon glyphicon-warning-sign'></span>")

        setattr(s, "state", state)
        setattr(s, "icon", icon)

    return render_template(
        "reserva_fixa/main.html",
        user=user,
        semestres=semestres,
        day=today
    )


@bp.route("/semestre/<int:id_semestre>")
@reserva_fixa_required
def get_semestre(id_semestre):
    userid, user = _current_user()
    semestre = _get_semestre_or_403(id_semestre, userid, user.perm)

    turnos = db.session.execute(
        select(Turnos).order_by(Turnos.horario_inicio)
    ).scalars().all()

    if not turnos:
        flash("cadastre ao menos 1 turno", "danger")
        return redirect(url_for("default.home"))

    return render_template(
        "reserva_fixa/semestre.html",
        user=user,
        semestre=semestre,
        turnos=turnos,
        day=date.today()
    )


@bp.route('/semestre/<int:id_semestre>/turno/lab')
@bp.route('/semestre/<int:id_semestre>/turno/lab/<int:id_lab>')
@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>/lab')
@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>/lab/<int:id_lab>')
@reserva_fixa_required
def get_lab(id_semestre, id_turno=None, id_lab=None):
    return (
        _get_lab_especifico(id_semestre, id_turno, id_lab)
        if id_lab else
        _get_lab_geral(id_semestre, id_turno)
    )


def _get_lab_geral(id_semestre, id_turno):
    userid, user = _current_user()
    semestre = _get_semestre_or_403(id_semestre, userid, user.perm)

    turno = db.get_or_404(Turnos, id_turno) if id_turno else None
    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    locais = get_laboratorios(bool(user.perm & PERM_ADMIN))

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
        locais=get_laboratorios(bool(user.perm & PERM_ADMIN)),
        aulas_extras=get_aulas_extras(semestre, turno)
    )

    return render_template("reserva_fixa/especifico.html", user=user, **extras)


@bp.route("/semestre/<int:id_semestre>", methods=["POST"])
@reserva_fixa_required
def efetuar_reserva(id_semestre):
    userid = session.get("userid")
    user = db.get_or_404(Usuarios, userid)
    semestre = db.get_or_404(Semestres, id_semestre)

    perm = db.session.get(Permissoes, userid)

    responsavel = none_if_empty(request.form.get("responsavel"))
    responsavel_especial = none_if_empty(request.form.get("responsavel_especial"))

    if not perm or not (perm.permissao & PERM_ADMIN):
        responsavel = user.id_pessoa
        responsavel_especial = None

    reservas = [
        _parse_reserva_key(k)
        for k, v in request.form.items()
        if k.startswith("reserva") and v == "on"
    ]

    if not reservas:
        flash("voce não selecionou reserva alguma", "warning")
        return redirect(url_for("default.home"))

    if (not perm or not (perm.permissao & PERM_ADMIN)) and _has_conflict(semestre, reservas, user):
        abort(409, description="so é possivel reservar 1 laboratorio por professor")

    try:
        criadas = []

        for lab, aula in reservas:
            r = Reservas_Fixas(
                id_responsavel=responsavel,
                id_responsavel_especial=responsavel_especial,
                id_reserva_local=lab,
                id_reserva_aula=aula,
                id_reserva_semestre=semestre.id_semestre,
                finalidade_reserva=FinalidadeReservaEnum(request.form.get("finalidade_reserva")),
                observacoes=none_if_empty(request.form.get("observacoes")),
                descricao=none_if_empty(request.form.get("descricao"))
            )
            db.session.add(r)
            criadas.append(r)

        db.session.flush()

        for r in criadas:
            registrar_log_generico_usuario(userid, "Inserção", r, observacao="atraves de reserva")

        db.session.commit()

        flash("reserva efetuada com sucesso", "success")

    except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
        _handle_db_error(e, "Erro ao efetuar reserva")
    except ValueError as e:
        _handle_db_error(e, "Erro ao efetuar reserva")

    return redirect(url_for("default.home"))