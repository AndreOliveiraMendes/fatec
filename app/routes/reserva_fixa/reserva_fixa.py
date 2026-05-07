from datetime import date
from urllib.parse import urlparse

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from markupsafe import Markup
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.general import none_if_empty
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.decorators.decorators import reserva_fixa_required
from app.extensions import db
from app.models.aulas import Semestres, Turnos
from app.models.reservas.reservas_laboratorios import Reservas_Fixas
from app.models.usuarios import Permissoes, Usuarios

from .handlers import (_current_user, _get_lab_especifico, _get_lab_geral,
                       _get_semestre_or_403, _handle_db_error, _has_conflict,
                       _parse_reserva_key)

bp = Blueprint('reservas_semanais', __name__, url_prefix="/reserva_fixa")

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
            if not (user and user.perm.has(Permission.ADMIN)):
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

@bp.route("/semestre/<int:id_semestre>", methods=["POST"])
@reserva_fixa_required
def efetuar_reserva(id_semestre):
    userid = session.get("userid")
    user = db.get_or_404(Usuarios, userid)
    semestre = db.get_or_404(Semestres, id_semestre)

    perm = db.session.get(Permissoes, userid)

    responsavel = none_if_empty(request.form.get("responsavel"))
    responsavel_especial = none_if_empty(request.form.get("responsavel_especial"))

    if not perm or not (perm.permissao & Permission.ADMIN):
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

    if (not perm or not (perm.permissao & Permission.ADMIN)) and _has_conflict(semestre, reservas, user):
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
                id_finalidade_reserva=request.form.get("id_finalidade_reserva", type=int),
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

    except DB_ERRORS as e:
        _handle_db_error(e, "Erro ao efetuar reserva")
    except ValueError as e:
        _handle_db_error(e, "Erro ao efetuar reserva")

    return redirect(url_for("default.home"))