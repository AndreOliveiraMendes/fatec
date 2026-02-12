import re
from collections import Counter
from datetime import date
from typing import Sequence, Set, Tuple, cast
from urllib.parse import urlparse

import mysql
from flask import (Blueprint, Response, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from markupsafe import Markup
from mysql.connector import DatabaseError, OperationalError, connect
from sqlalchemy import between, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (builder_helper_fixa, check_local,
                                          get_responsavel_reserva,
                                          get_unique_or_500, get_user_info,
                                          none_if_empty,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import (get_aulas_ativas_por_semestre, get_aulas_extras,
                              get_laboratorios, get_pessoas,
                              get_usuarios_especiais)
from app.auxiliar.decorators import admin_required, reserva_fixa_required
from app.models import (FinalidadeReservaEnum, Locais, Permissoes,
                        Reservas_Fixas, Semestres, Turnos, Usuarios, db)
from config.general import (DISPONIBILIDADE_DATABASE, DISPONIBILIDADE_HOST,
                            DISPONIBILIDADE_PASSWORD, DISPONIBILIDADE_USER)

bp = Blueprint('reservas_semanais', __name__, url_prefix="/reserva_fixa")


def get_prioridade():
    try:
        with connect(
            host=DISPONIBILIDADE_HOST,
            user=DISPONIBILIDADE_USER,
            password=DISPONIBILIDADE_PASSWORD,
            database=DISPONIBILIDADE_DATABASE
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT professor
                    FROM grade
                    INNER JOIN disciplina ON disciplina.codigo = grade.disciplina
                    WHERE professor is not NULL and lab = 1
                    ORDER BY professor
                """)
                rows = cast(Sequence[tuple[int]], cursor.fetchall())
                return True, {row[0] for row in rows}
    except (DatabaseError, OperationalError) as e:
        current_app.logger.error(f"erro ao ler banco, rodando sem regra de prioridade:{e}")
        return False, None

def check_semestre(semestre:Semestres, userid, perm:int):
    if perm&PERM_ADMIN > 0:
        return
    today = date.today()
    if today < semestre.data_inicio_reserva or today > semestre.data_fim_reserva:
        abort(403, description="Semestre fora do período de reservas.")
    if (today - semestre.data_inicio_reserva).days < semestre.dias_de_prioridade:
        has_priority, prioridade = get_prioridade()
        user = db.get_or_404(Usuarios, userid)
        if has_priority and prioridade is not None and user.pessoa.id_pessoa not in prioridade:
            abort(403, description="Usuário não se enquadra na regra de prioridade.")

@bp.route('/')
@reserva_fixa_required
def main_page():
    userid = session.get('userid')
    user = get_user_info(userid)
    extras = {}
    sel_semestre = select(Semestres).order_by(Semestres.data_inicio)
    semestres = db.session.execute(sel_semestre).scalars().all()
    if len(semestres) == 0:
        flash("cadastre ao menos um semestre", "danger")
        return redirect(url_for('default.home'))
    today = date.today()
    extras['semestres'] = semestres
    for semestre in semestres:
        state, icon = '', ''
        if today < semestre.data_inicio:
            state = 'success'
        elif today <= semestre.data_fim:
            state = 'primary'
        else:
            state = 'default'
        if today < semestre.data_inicio_reserva or today > semestre.data_fim_reserva:
            if not user or not user.perm&PERM_ADMIN > 0:
                state += ' disabled'
            icon = Markup("<span class='glyphicon glyphicon-lock'></span>")
        elif (today - semestre.data_inicio_reserva).days < semestre.dias_de_prioridade:
            icon = Markup("<span class='glyphicon glyphicon-warning-sign'></span>")
        setattr(semestre, "state", state)
        setattr(semestre, "icon", icon)
    extras['day'] = today
    return render_template('reserva_fixa/main.html', user=user, **extras)

@bp.route('/semestre/<int:id_semestre>')
@reserva_fixa_required
def get_semestre(id_semestre):
    userid = session.get('userid')
    user = get_user_info(userid)
    if not user:
        abort(403, description="Usuário não autenticado.")
    semestre = db.get_or_404(Semestres, id_semestre)
    check_semestre(semestre, userid, user.perm)
    today = date.today()
    extras = {'semestre':semestre, 'day':today}
    sel_turnos = select(Turnos).order_by(Turnos.horario_inicio)
    turnos = db.session.execute(sel_turnos).scalars().all()
    if len(turnos) == 0:
        flash("cadastre ao menos 1 turno", "danger")
        return redirect(url_for('default.home'))
    extras['turnos'] = turnos
    return render_template('reserva_fixa/semestre.html', user=user, **extras)

@bp.before_request
def return_counter():
    if request.endpoint == "reservas_semanais.get_lab":
        referer = request.headers.get("Referer", "")

        path = urlparse(referer).path
        parts = path.strip("/").split("/")

        dentro = (
            len(parts) in (6, 7)
            and parts[0] == "reserva_fixa"
            and parts[1] == "semestre"
            and parts[2].isdigit()
            and parts[3] == "turno"
            and parts[4].isdigit()
            and parts[5] == "lab"
            and (len(parts) == 6 or parts[6].isdigit())
        )

        if dentro:
            session["contador"] = session.get("contador", 0) + 1
        else:
            session["contador"] = 1
    else:
        session.pop("contador", None)

@bp.route('/semestre/<int:id_semestre>/turno/lab')
@bp.route('/semestre/<int:id_semestre>/turno/lab/<int:id_lab>')
@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>/lab')
@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>/lab/<int:id_lab>')
@reserva_fixa_required
def get_lab(id_semestre, id_turno=None, id_lab=None):
    if id_lab is None:
        return get_lab_geral(id_semestre, id_turno)
    else:
        return get_lab_especifico(id_semestre, id_turno, id_lab)

def get_lab_geral(id_semestre, id_turno=None):
    userid = session.get('userid')
    user = get_user_info(userid)
    if not user:
        abort(403, description="Usuário não autenticado.")
    semestre = db.get_or_404(Semestres, id_semestre)
    check_semestre(semestre, userid, user.perm)
    turno = db.get_or_404(Turnos, id_turno) if id_turno is not None else id_turno
    today = date.today()
    extras = {'semestre':semestre, 'turno':turno, 'day':today}
    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    locais = get_laboratorios(user.perm&PERM_ADMIN > 0)
    if len(aulas) == 0 or len(locais) == 0:
        if len(aulas) == 0:
            flash("não há horarios disponiveis nesse turno", "danger")
        if len(locais) == 0:
            flash("não há local disponiveis para reserva", "danger")
        return redirect(url_for('default.home'))
    
    extras['locais'] = locais
    extras['aulas'] = aulas
    extras['finalidade_reserva'] = FinalidadeReservaEnum
    extras['aulas_extras'] = get_aulas_extras(semestre, turno)
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    extras['contador'] = session.get('contador')
    return render_template('reserva_fixa/geral.html', user=user, **extras)

def get_lab_especifico(id_semestre, id_turno, id_lab):
    userid = session.get('userid')
    user = get_user_info(userid)
    if not user:
        abort(403, description="Usuário não autenticado.")
    semestre = db.get_or_404(Semestres, id_semestre)
    check_semestre(semestre, userid, user.perm)
    turno = db.get_or_404(Turnos, id_turno) if id_turno is not None else id_turno
    local = db.get_or_404(Locais, id_lab)
    check_local(local, user.perm)
    today = date.today()
    extras = {'semestre':semestre, 'turno':turno, 'local':local, 'day':today}
    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    if len(aulas) == 0:
        flash("não há horarios disponiveis nesse turno", "danger")
        return redirect(url_for('default.home'))
    builder_helper_fixa(extras, aulas)
    extras['aulas'] = aulas
    extras['locais'] = get_laboratorios(user.perm&PERM_ADMIN > 0)
    extras['finalidade_reserva'] = FinalidadeReservaEnum
    extras['aulas_extras'] = get_aulas_extras(semestre, turno)
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    extras['contador'] = session.get('contador')
    return render_template('reserva_fixa/especifico.html', user=user, **extras)

@bp.route('/semestre/<int:id_semestre>', methods=['POST'])
@reserva_fixa_required
def efetuar_reserva(id_semestre):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    finalidade_reserva = request.form.get('finalidade_reserva')
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))
    responsavel = none_if_empty(request.form.get('responsavel'))
    responsavel_especial = none_if_empty(request.form.get('responsavel_especial'))
    perm = db.session.get(Permissoes, userid)
    if not perm or perm.permissao & PERM_ADMIN == 0:
        responsavel = user.id_pessoa
        responsavel_especial = None
    checks = [key for key, value in request.form.items() if key.startswith('reserva') and value == 'on']
    if not checks:
        flash("voce não selecionou reserva alguma", "warning")
        return redirect(url_for('default.home'))
    try:
        reservas_efetuadas = []
        for check in checks:
            lab, aula = map(int, check.replace('reserva[', '').replace(']', '').split(','))

            reserva = Reservas_Fixas(
                id_responsavel = responsavel,
                id_responsavel_especial = responsavel_especial,
                id_reserva_local = lab,
                id_reserva_aula = aula,
                id_reserva_semestre = semestre.id_semestre,
                finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva),
                observacoes = observacoes
            )
            if descricao:
                reserva.descricao = descricao
            db.session.add(reserva)
            reservas_efetuadas.append(reserva)

        db.session.flush()
        for reserva in reservas_efetuadas:
            registrar_log_generico_usuario(userid, 'Inserção', reserva, observacao='atraves de reserva')

        db.session.commit()
        flash("reserva efetuada com sucesso", "success")
        for reserva in reservas_efetuadas:
            current_app.logger.info(f"reserva efetuada com sucesso para {reserva} por {userid}")
    except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(e.orig)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{e}")
    except ValueError as ve:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(ve)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{ve}")

    return redirect(url_for('default.home'))