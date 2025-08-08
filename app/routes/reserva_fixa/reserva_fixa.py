from collections import Counter
from datetime import date

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from markupsafe import Markup
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_responsavel_reserva,
                                          get_user_info, none_if_empty,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import (get_aulas_ativas_por_semestre, get_aulas_extras,
                              get_laboratorios, get_pessoas,
                              get_usuarios_especiais)
from app.auxiliar.decorators import reserva_fixa_required
from app.models import (Permissoes, Reservas_Fixas, Semestres, TipoReservaEnum,
                        Turnos, Usuarios, db)

bp = Blueprint('reservas_semanais', __name__, url_prefix="/reserva_fixa")

def check_semestre(semestre:Semestres, perm:Permissoes):
    today = date.today()
    if (today < semestre.data_inicio_reserva or today > semestre.data_fim_reserva) and not perm&PERM_ADMIN > 0:
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
    check_semestre(semestre, perm)
    today = date.today()
    extras = {'semestre':semestre, 'day':today}
    sel_turnos = select(Turnos).order_by(Turnos.horario_inicio)
    turnos = db.session.execute(sel_turnos).scalars().all()
    if len(turnos) == 0:
        flash("cadastre ao menos 1 turno", "danger")
        return redirect(url_for('default.home'))
    extras['turnos'] = turnos
    return render_template('reserva_fixa/semestre.html', username=username, perm=perm, **extras)

@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>')
@reserva_fixa_required
def get_turno(id_semestre, id_turno):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    check_semestre(semestre, perm)
    turno = db.get_or_404(Turnos, id_turno)
    today = date.today()
    extras = {'semestre':semestre, 'turno':turno, 'day':today}
    aulas = get_aulas_ativas_por_semestre(semestre, turno)
    laboratorios = get_laboratorios(False)
    if len(aulas) == 0 or len(laboratorios) == 0:
        if len(aulas) == 0:
            flash("não há horarios disponiveis nesse turno", "danger")
        if len(laboratorios) == 0:
            flash("não há laboratorio disponiveis para reserva", "danger")
        return redirect(url_for('default.home'))
    extras['laboratorios'] = laboratorios
    extras['aulas'] = aulas
    contagem_dias = Counter()
    label = {}
    head2 = []

    for info in aulas:
        semana = info[2]
        contagem_dias[semana.id_semana] += 1
        label[semana.id_semana] = semana.nome_semana
        head2.append(info[1].selector_identification)

    head1 = [(label[id_semana], count) for id_semana, count in contagem_dias.items()]
    extras['head1'] = head1
    extras['head2'] = head2
    sel_reservas = select(Reservas_Fixas).where(Reservas_Fixas.id_reserva_semestre == id_semestre)
    reservas = db.session.execute(sel_reservas).scalars().all()
    helper = {}
    for r in reservas:
        title = get_responsavel_reserva(r)
        helper[(r.id_reserva_laboratorio, r.id_reserva_aula)] = title
    extras['helper'] = helper
    extras['tipo_reserva'] = TipoReservaEnum
    extras['aulas_extras'] = get_aulas_extras(semestre, turno)
    extras['responsavel'] = get_pessoas()
    extras['responsavel_especial'] = get_usuarios_especiais()
    return render_template('reserva_fixa/turno.html', username=username, perm=perm, **extras)

@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>', methods=['POST'])
@reserva_fixa_required
def efetuar_reserva(id_semestre, id_turno):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    tipo_reserva = request.form.get('tipo_reserva')
    observacoes = none_if_empty(request.form.get('observacoes'))
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
                id_reserva_laboratorio = lab,
                id_reserva_aula = aula,
                id_reserva_semestre = semestre.id_semestre,
                tipo_reserva = TipoReservaEnum(tipo_reserva),
                observacoes = observacoes
            )
            db.session.add(reserva)
            reservas_efetuadas.append(reserva)

        db.session.flush()
        for reserva in reservas_efetuadas:
            registrar_log_generico_usuario(userid, 'Inserção', reserva, observacao='atraves de reserva')

        db.session.commit()
        flash("reserva efetuada com sucesso", "success")
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(e.orig)}", "danger")
    except ValueError as ve:
        db.session.rollback()
        flash(f"Erro ao efetuar reserva:{str(ve)}", "danger")

    return redirect(url_for('default.home'))
