from flask import Blueprint, flash, session, render_template, redirect, url_for, request
from sqlalchemy import select
from datetime import date, datetime
from app.models import db, Semestres, Turnos
from app.auxiliar.auxiliar_routes import get_user_info

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
    extras = {'semestre':semestre}
    sel_turnos = select(Turnos).order_by(Turnos.horario_inicio)
    turnos = db.session.execute(sel_turnos).scalars().all()
    if len(turnos) == 0:
        flash("cadastre ao menos 1 turno", "danger")
        return redirect(url_for('default.home'))
    now = datetime.now()
    extras['turnos'] = turnos
    extras['time'] = now.time()
    return render_template('reserva_fixa/semestre.html', username=username, perm=perm, **extras)

@bp.route('/semestre/<int:id_semestre>/turno/<int:id_turno>')
def get_turno(id_semestre, id_turno):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    semestre = db.get_or_404(Semestres, id_semestre)
    turno = db.get_or_404(Turnos, id_turno)
    extras = {'semestre':semestre, 'turno':turno}

    return render_template('reserva_fixa/turno.html', username=username, perm=perm, **extras)