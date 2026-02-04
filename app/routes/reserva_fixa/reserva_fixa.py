from collections import Counter
from datetime import date
from typing import Sequence, Set, Tuple, cast

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
        abort(403)
    if (today - semestre.data_inicio_reserva).days < semestre.dias_de_prioridade:
        has_priority, prioridade = get_prioridade()
        user = db.get_or_404(Usuarios, userid)
        if has_priority and prioridade is not None and user.pessoa.id_pessoa not in prioridade:
            abort(403)

def build_table_headers_geral(aulas, extras, id_turno=None):
    contagem_dias = Counter()
    contagem_turnos = Counter()
    label = {}
    head2 = []

    for info in aulas:
        aula = info[1]
        semana = info[2]

        # Contagem por dia da semana
        contagem_dias[semana.id_semana] += 1

        # Contagem por turno (somente se não houver turno fixo)
        if id_turno is None:
            turno = get_unique_or_500(
                Turnos,
                between(aula.horario_inicio, Turnos.horario_inicio, Turnos.horario_fim)
            )
            contagem_turnos[(semana.id_semana, turno)] += 1

        # Labels e cabeçalho secundário
        label[semana.id_semana] = semana.nome_semana
        head2.append(aula.selector_identification)

    extras["head1"] = [
        (label[id_semana], count)
        for id_semana, count in contagem_dias.items()
    ]
    extras["head2"] = head2
    extras["head_turno"] = contagem_turnos

def build_table_semanas_aulas(aulas, extras):
    table_aulas = []
    table_semanas = []

    # 🔹 Coleta aulas únicas
    for info in aulas:
        _, aula, _ = info
        if aula not in table_aulas:
            table_aulas.append(aula)

    # 🔹 Ordena aulas por horário
    table_aulas.sort(key=lambda e: e.horario_inicio)
    size = len(table_aulas)

    # 🔹 Monta estrutura por semana × aula
    for info in aulas:
        _, aula, semana = info

        # Procura semana existente
        index_semana = None
        for i, v in enumerate(table_semanas):
            if v["semana"] == semana:
                index_semana = i
                break
        else:
            table_semanas.append({
                "semana": semana,
                "infos": [None] * size
            })
            index_semana = len(table_semanas) - 1

        # Procura índice da aula
        index_aula = None
        for i, v in enumerate(table_aulas):
            if v == aula:
                index_aula = i
                break

        table_semanas[index_semana]["infos"][index_aula] = info

    extras["head1"] = table_aulas
    extras["semanas"] = table_semanas

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
        abort(403)
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
        session["contador"] = session.get("contador", 0) + 1
    else:
        session.pop("contador", None)

@bp.before_app_request
def clear_counter():
    if not request.endpoint:
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
        abort(403)
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
    build_table_headers_geral(aulas, extras, id_turno)
    extras['helper'] = builder_helper_fixa(id_semestre)
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
        abort(403)
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
    extras['aulas'] = aulas
    extras['locais'] = get_laboratorios(user.perm&PERM_ADMIN > 0)
    build_table_semanas_aulas(aulas, extras)
    extras['helper'] = builder_helper_fixa(id_semestre, id_lab)
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

# helper api (to be moved soon)
@bp.route('/api/reserva/<int:id_reserva>')
@reserva_fixa_required
@admin_required
def get_reserva_info(id_reserva):
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    responsavel = get_responsavel_reserva(reserva)
    return {
        "id_reserva": reserva.id_reserva_fixa,
        "id_semestre": reserva.id_reserva_semestre,
        "id_responsavel": reserva.id_responsavel,
        "id_responsavel_especial": reserva.id_responsavel_especial,
        "id_local": reserva.id_reserva_local,
        "id_aula_ativa": reserva.id_reserva_aula,
        "finalidade": reserva.finalidade_reserva.value,
        "observacoes": reserva.observacoes,
        "descricao": reserva.descricao,
        "semestre": reserva.semestre.nome_semestre,
        "responsavel": responsavel,
        "horario": reserva.aula_ativa.selector_identification,
        "local": reserva.local.nome_local
    }
    
@reserva_fixa_required
@admin_required
@bp.route('/api/reserva/update/<int:id_reserva>', methods=['POST'])
def update_reserva(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    data = request.form

    responsavel = none_if_empty(data.get('id_responsavel'), int)
    responsavel_especial = none_if_empty(data.get('id_responsavel_especial'), int)
    local = none_if_empty(data.get('id_local'), int)
    aula = none_if_empty(data.get('id_aula'), int)
    finalidade_reserva = data.get('finalidade')
    observacoes = data.get('observacoes')
    descricao = data.get('descricao')
    if local is None or aula is None:
        return Response(status=400)

    try:
        reserva.id_responsavel = responsavel
        reserva.id_responsavel_especial = responsavel_especial
        reserva.id_reserva_local = local
        reserva.id_reserva_aula = aula
        reserva.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
        reserva.observacoes = observacoes
        reserva.descricao = descricao

        registrar_log_generico_usuario(
            userid,
            'Edição',
            reserva,
            observacao='através de reserva'
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva atualizada com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        current_app.logger.error(f"falha ao atualizar reserva: {e}")
        return Response(status=500)
    except ValueError as ve:
        db.session.rollback()
        current_app.logger.error(f"falha ao atualizar reserva: {ve}")
        return Response(status=500)

@reserva_fixa_required
@admin_required
@bp.route('/api/reserva/delete/<int:id_reserva>', methods=['DELETE'])
def delete_reserva(id_reserva):
    userid = session.get('userid')
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)

    try:
        db.session.delete(reserva)
        registrar_log_generico_usuario(
            userid,
            'Exclusão',
            reserva,
            observacao='através de reserva'
        )
        db.session.commit()
        current_app.logger.info(
            f"reserva removida com sucesso para {reserva} por {userid}"
        )

        return Response(status=204)

    except (DataError, IntegrityError, InterfaceError,
            InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        current_app.logger.error(f"falha ao remover reserva: {e}")
        return Response(status=500)