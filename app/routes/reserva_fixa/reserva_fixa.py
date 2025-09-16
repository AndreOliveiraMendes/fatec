from collections import Counter
from datetime import date

import mysql
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from markupsafe import Markup
from mysql.connector import DatabaseError, OperationalError
from sqlalchemy import between, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (check_local, get_responsavel_reserva,
                                          get_unique_or_500, get_user_info,
                                          none_if_empty,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import (get_aulas_ativas_por_semestre, get_aulas_extras,
                              get_laboratorios, get_pessoas,
                              get_usuarios_especiais)
from app.auxiliar.decorators import reserva_fixa_required
from app.models import (FinalidadeReservaEnum, Locais, Permissoes,
                        Reservas_Fixas, Semestres, Turnos, Usuarios, db)
from config.general import (DISPONIBILIDADE_DATABASE, DISPONIBILIDADE_HOST,
                            DISPONIBILIDADE_PASSWORD, DISPONIBILIDADE_USER)

bp = Blueprint('reservas_semanais', __name__, url_prefix="/reserva_fixa")


def get_prioridade():
    try:
        with mysql.connector.connect(
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
                return True, cursor.fetchall()
    except (DatabaseError, OperationalError) as e:
        current_app.logger.error(f"erro ao ler banco, rodando sem regra de prioridade:{e}")
        return False, None

def check_semestre(semestre:Semestres, userid, perm:Permissoes):
    if perm&PERM_ADMIN > 0:
        return
    today = date.today()
    if today < semestre.data_inicio_reserva or today > semestre.data_fim_reserva:
        abort(403)
    if (today - semestre.data_inicio_reserva).days < semestre.dias_de_prioridade:
        has_priority, prioridade = get_prioridade()
        user = db.get_or_404(Usuarios, userid)
        if has_priority and not user.pessoas.id_pessoa in prioridade:
            abort(403)

@bp.route('/')
@reserva_fixa_required
def main_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
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
            if not perm&PERM_ADMIN > 0:
                state += ' disabled'
            icon = Markup("<span class='glyphicon glyphicon-lock'></span>")
        elif (today - semestre.data_inicio_reserva).days < semestre.dias_de_prioridade:
            icon = Markup("<span class='glyphicon glyphicon-warning-sign'></span>")
        semestre.state = state
        semestre.icon = icon
    extras['day'] = today
    return render_template('reserva_fixa/main.html', username=username, perm=perm, **extras)

@bp.route('/semestre/<int:id_semestre>')
@reserva_fixa_required
def get_semestre(id_semestre):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    check_semestre(semestre, userid, perm)
    today = date.today()
    extras = {'semestre':semestre, 'day':today}
    sel_turnos = select(Turnos).order_by(Turnos.horario_inicio)
    turnos = db.session.execute(sel_turnos).scalars().all()
    if len(turnos) == 0:
        flash("cadastre ao menos 1 turno", "danger")
        return redirect(url_for('default.home'))
    extras['turnos'] = turnos
    return render_template('reserva_fixa/semestre.html', username=username, perm=perm, **extras)

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
    username, perm = get_user_info(userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    check_semestre(semestre, userid, perm)
    turno = db.get_or_404(Turnos, id_turno) if id_turno is not None else id_turno
    today = date.today()
    extras = {'semestre':semestre, 'turno':turno, 'day':today}
    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    locais = get_laboratorios(perm&PERM_ADMIN)
    if len(aulas) == 0 or len(locais) == 0:
        if len(aulas) == 0:
            flash("não há horarios disponiveis nesse turno", "danger")
        if len(locais) == 0:
            flash("não há local disponiveis para reserva", "danger")
        return redirect(url_for('default.home'))
    extras['locais'] = locais
    extras['aulas'] = aulas
    contagem_dias = Counter()
    contagem_turnos = Counter()
    label = {}
    head2 = []

    for info in aulas:
        semana = info[2]
        contagem_dias[semana.id_semana] += 1
        if id_turno is None:
            turno = get_unique_or_500(Turnos, between(info[1].horario_inicio, Turnos.horario_inicio, Turnos.horario_fim))
            contagem_turnos[(semana.id_semana, turno)] += 1
        label[semana.id_semana] = semana.nome_semana
        head2.append(info[1].selector_identification)

    head1 = [(label[id_semana], count) for id_semana, count in contagem_dias.items()]
    extras['head1'] = head1
    extras['head2'] = head2
    extras['head_turno'] = contagem_turnos
    sel_reservas = select(Reservas_Fixas).where(Reservas_Fixas.id_reserva_semestre == id_semestre)
    reservas = db.session.execute(sel_reservas).scalars().all()
    helper = {}
    for r in reservas:
        title = get_responsavel_reserva(r)
        helper[(r.id_reserva_local, r.id_reserva_aula)] = title
    extras['helper'] = helper
    extras['finalidade_reserva'] = FinalidadeReservaEnum
    extras['aulas_extras'] = get_aulas_extras(semestre, turno)
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    extras['contador'] = session.get('contador')
    return render_template('reserva_fixa/geral.html', username=username, perm=perm, **extras)

def get_lab_especifico(id_semestre, id_turno, id_lab):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    check_semestre(semestre, userid, perm)
    turno = db.get_or_404(Turnos, id_turno) if id_turno is not None else id_turno
    local = db.get_or_404(Locais, id_lab)
    check_local(local, perm)
    today = date.today()
    extras = {'semestre':semestre, 'turno':turno, 'local':local, 'day':today}
    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    if len(aulas) == 0:
        flash("não há horarios disponiveis nesse turno", "danger")
        return redirect(url_for('default.home'))
    table_aulas = []
    table_semanas = []
    for info in aulas:
        _, aula, _ = info
        if not aula in table_aulas:
            table_aulas.append(aula)
    table_aulas.sort(key = lambda e:e.horario_inicio)
    size = len(table_aulas)
    for info in aulas:
        _, aula, semana = info
        index_semana, index_aula = None, None
        for i, v in enumerate(table_semanas):
            if v['semana'] == semana:
                index_semana = i
                break
        else:
            table_semanas.append({'semana':semana, 'infos':[None]*size})
            index_semana = len(table_semanas) - 1
        for i, v in enumerate(table_aulas):
            if v == aula:
                index_aula = i
                break
        table_semanas[index_semana]['infos'][index_aula] = info
    extras['aulas'] = table_aulas
    extras['semanas'] = table_semanas
    extras['finalidade_reserva'] = FinalidadeReservaEnum
    extras['aulas_extras'] = get_aulas_extras(semestre, turno)
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    sel_reservas = select(Reservas_Fixas).where(
        Reservas_Fixas.id_reserva_semestre == id_semestre,
        Reservas_Fixas.id_reserva_local == id_lab)
    reservas = db.session.execute(sel_reservas).scalars().all()
    helper = {}
    for r in reservas:
        title = get_responsavel_reserva(r)
        helper[(r.id_reserva_local, r.id_reserva_aula)] = title
    extras['helper'] = helper
    extras['finalidade_reserva'] = FinalidadeReservaEnum
    extras['aulas_extras'] = get_aulas_extras(semestre, turno)
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    extras['contador'] = session.get('contador')
    extras['locais'] = get_laboratorios(perm&PERM_ADMIN)
    return render_template('reserva_fixa/especifico.html', username=username, perm=perm, **extras)

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
    tipo_responsavel = None
    if responsavel_especial is None:
        tipo_responsavel = 0
    elif responsavel is None:
        tipo_responsavel = 1
    else:
        tipo_responsavel = 2
    perm = db.session.get(Permissoes, userid)
    if not perm or perm.permissao & PERM_ADMIN == 0:
        responsavel = user.id_pessoa
        responsavel_especial = None
        tipo_responsavel = 0
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
                tipo_responsavel = tipo_responsavel,
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
        current_app.logger.info(f"reserva efetuada com sucesso para {reserva}")
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(e.orig)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{e}")
    except ValueError as ve:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(ve)}", "danger")
        current_app.logger.error(f"falha ao realizar reserva:{e}")

    return redirect(url_for('default.home'))