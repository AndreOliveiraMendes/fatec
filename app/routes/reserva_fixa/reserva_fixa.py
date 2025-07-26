from flask import Blueprint, flash, session, render_template, redirect, url_for, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import date, datetime
from app.models import db, Semestres, Turnos, Reservas_Fixas, TipoReservaEnum, Usuarios, \
    Pessoas, Usuarios_Especiais
from app.auxiliar.auxiliar_routes import get_user_info, registrar_log_generico_usuario
from app.auxiliar.dao import get_aulas_ativas_reserva, get_laboratorios
from collections import Counter

bp = Blueprint('reservas_semanais', __name__, url_prefix="/reserva_fixa")


@bp.route('/')
def main_page():
    url = 'reservas_semanais.main_page'
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {'url':url}
    sel_semestre = select(Semestres).order_by(Semestres.data_inicio)
    semestres = db.session.execute(sel_semestre).scalars().all()
    if len(semestres) == 0:
        flash("cadastre ao menos um semestre", "danger")
        return redirect(url_for('default.home'))
    today = date.today()
    extras['semestres'] = semestres
    for semestre in semestres:
        state = ''
        if today < semestre.data_inicio:
            state = 'success'
        elif today <= semestre.data_fim:
            state = 'primary'
        else:
            state = 'default'
        semestre.state = state
    extras['day'] = today
    return render_template('reserva_fixa/main.html', username=username, perm=perm, **extras)

@bp.route('/semestre/<int:id_semestre>')
def get_semestre(id_semestre):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    today = date.today()
    extras = {'semestre':semestre, 'day':today}
    sel_turnos = select(Turnos).order_by(Turnos.horario_inicio)
    turnos = db.session.execute(sel_turnos).scalars().all()
    if len(turnos) == 0:
        flash("cadastre ao menos 1 turno", "danger")
        return redirect(url_for('default.home'))
    now = datetime.now()
    extras['turnos'] = turnos
    return render_template('reserva_fixa/semestre.html', username=username, perm=perm, **extras)

@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>')
def get_turno(id_semestre, id_turno):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    turno = db.get_or_404(Turnos, id_turno)
    today = date.today()
    extras = {'semestre':semestre, 'turno':turno, 'day':today}
    aulas = get_aulas_ativas_reserva(today, turno)
    contagem_dias = Counter(info[2].id_semana for info in aulas)
    head1 = {
        info[2].id_semana: (info[2].nome_semana, contagem_dias[info[2].id_semana])
        for info in aulas
    }
    head2 = [info[1].selector_identification for info in aulas]
    extras['head1'] = head1
    extras['head2'] = head2
    laboratorios = get_laboratorios(False)
    if len(aulas) == 0 or len(laboratorios) == 0:
        if len(aulas) == 0:
            flash("não há horarios disponiveis nesse turno", "danger")
        if len(laboratorios) == 0:
            flash("não há laboratorio disponiveis para reserva", "danger")
        return redirect(url_for('default.home'))
    extras['laboratorios'] = laboratorios
    extras['aulas'] = aulas
    sel_reservas = select(Reservas_Fixas).where(Reservas_Fixas.id_reserva_semestre == id_semestre)
    reservas = db.session.execute(sel_reservas).scalars().all()
    helper = {}
    for r in reservas:
        title = 'reservado por '
        empty = True
        if r.tipo_responsavel == 0 or r.tipo_responsavel == 2:
            responsavel = db.get_or_404(Pessoas, r.id_responsavel)
            title += responsavel.nome_pessoa
            empty = False
        if r.tipo_responsavel == 1 or r.tipo_responsavel == 2:
            responsavel = db.get_or_404(Usuarios_Especiais, r.id_responsavel_especial)
            if empty:
                title += responsavel.nome_usuario_especial
            else:
                title += f"({responsavel.nome_usuario_especial})"
        helper[(r.id_reserva_laboratorio, r.id_reserva_aula)] = title
    extras['helper'] = helper
    extras['tipo_reserva'] = TipoReservaEnum
    return render_template('reserva_fixa/turno.html', username=username, perm=perm, **extras)

@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>', methods=['POST'])
def efetuar_reserva(id_semestre, id_turno):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    tipo_reserva = request.form.get('tipo_reserva')
    checks = [key for key, value in request.form.items() if key.startswith('reserva') and value == 'on']
    try:
        reservas_efetuadas = []
        for check in checks:
            lab, aula = map(int, check.replace('reserva[', '').replace(']', '').split(','))

            reserva = Reservas_Fixas(
                id_responsavel = user.pessoas.id_pessoa,
                id_responsavel_especial = None,
                tipo_responsavel = 0,
                id_reserva_laboratorio = lab,
                id_reserva_aula = aula,
                id_reserva_semestre = semestre.id_semestre,
                tipo_reserva = TipoReservaEnum(tipo_reserva)
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