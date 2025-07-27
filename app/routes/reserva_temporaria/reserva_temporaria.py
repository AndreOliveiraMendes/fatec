from flask import Blueprint, flash, session, render_template, redirect, url_for, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import date, datetime
from app.models import db, TipoAulaEnum
from app.auxiliar.auxiliar_routes import get_user_info, registrar_log_generico_usuario, parse_date_string
from collections import Counter
from config.general import LOCAL_TIMEZONE

bp = Blueprint('reservas_esporádicas', __name__, url_prefix="/reserva_temporaria")

@bp.route('/', methods=['GET', 'POST'])
def main_page():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    extras = {}
    if request.method == 'GET':
        extras['tipo_aula'] = TipoAulaEnum
        today = date.today()
        extras['day'] = today
        return render_template('reserva_temporaria/main.html', username=username, perm=perm, **extras)
    else:
        dia_inicial = parse_date_string(request.form.get('dia_inicio'))
        dia_final = parse_date_string(request.form.get('dia_fim'))
        if dia_inicial > dia_final:
            dia_inicial, dia_final = dia_final, dia_inicial
        return render_template('reserva_temporaria/dias.html', username=username, perm=perm, **extras)

