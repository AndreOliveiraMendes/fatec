from copy import copy
from datetime import datetime

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from sqlalchemy import func, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_user_info, parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN
from app.auxiliar.dao import get_auditorios, get_reservas_auditorios
from app.auxiliar.decorators import reserva_auditorio_required
from app.models import (Reservas_Auditorios, StatusReservaAuditorioEnum,
                        Usuarios, db)
from config.general import LOCAL_TIMEZONE

bp = Blueprint('reservas_auditorios', __name__, url_prefix="/reserva_auditorio")

@bp.route('/')
@reserva_auditorio_required
def main_page():
    userid = session.get('userid')
    user = get_user_info(userid)
    today = datetime.now(LOCAL_TIMEZONE)
    extras = {'dia':today}
    extras['auditorios'] = get_auditorios()

    reserva_dia = parse_date_string(request.args.get('reserva-dia'))
    if not 'reserva-dia' in request.args:
        reserva_dia = today.date()
    extras['reserva_dia'] = reserva_dia

    conditions = []
    if reserva_dia:
        conditions.append(Reservas_Auditorios.dia_reserva == reserva_dia)
    extras['reservas_auditorios'] = get_reservas_auditorios(user.pessoa.id_pessoa, user.perm&PERM_ADMIN, *conditions)
    return render_template('reserva_auditorio/main.html', user=user, **extras)

def check_own_reserva(reserva:Reservas_Auditorios, user:Usuarios):
    if user.id_pessoa != reserva.id_responsavel and user.perm & PERM_ADMIN == 0:
        abort(403)

def check_role(user:Usuarios):
    if user.perm & PERM_ADMIN == 0:
        abort(403)

def check_unique_aprovada(reserva:Reservas_Auditorios):
    count_rtc = select(func.count()).select_from(Reservas_Auditorios).where(
        Reservas_Auditorios.id_reserva_auditorio != reserva.id_reserva_auditorio,
        Reservas_Auditorios.id_reserva_local == reserva.id_reserva_local,
        Reservas_Auditorios.id_reserva_aula == reserva.id_reserva_aula,
        Reservas_Auditorios.dia_reserva == reserva.dia_reserva,
        Reservas_Auditorios.status_reserva == StatusReservaAuditorioEnum.APROVADA
    )
    if db.session.scalar(count_rtc) > 0:
        abort(409, description="Já existe uma reserva aprovada para este auditório no mesmo horário.")


@bp.route('/atualizar_reserva/<int:id_reserva>', methods=['POST'])
@reserva_auditorio_required
def atualizar_status(id_reserva):
    """
    ("Aguardando", "Cancelada") -> ("Aguardando", "Cancelada")
    ("Aguardando", "Aprovada", "Reprovada") -> ("Aprovada", "Reprovada")
    """
    userid = session.get('userid')
    user = get_user_info(userid)
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    old_reserva = copy(reserva)
    old_status = reserva.status_reserva.value
    new_status = request.form.get('status')
    if old_status in ['Cancelada', 'Aguardando'] and new_status in ['Cancelada', 'Aguardando']:
        check_own_reserva(reserva, user)
        try:
            reserva.status_reserva = StatusReservaAuditorioEnum(new_status)

            db.session.flush()
            registrar_log_generico_usuario(userid, 'Edição', reserva, old_reserva, "atraves do painel", True)

            db.session.commit()
            flash("Reserva Atualizada com sucesso", "success")
        except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
            db.session.rollback()
            flash(f"Erro ao Atualizar:{str(e.orig)}", "danger")
        except ValueError as ve:
            db.session.rollback()
            flash(f"Erro ao Atualizar:{ve}", "danger")
    if old_status in ['Aguardando', 'Aprovada', 'Reprovada'] and new_status in ['Aprovada', 'Reprovada']:
        check_role(user)
        if new_status == 'Aprovada':
            check_unique_aprovada(reserva)
        try:
            reserva.status_reserva = StatusReservaAuditorioEnum(new_status)
            reserva.id_autorizador = user.id_pessoa

            db.session.flush()
            registrar_log_generico_usuario(userid, 'Edição', reserva, old_reserva, 'atraves de painel', True)

            db.session.commit()
            flash("Reserva Atualizada com sucesso", "success")
        except (DataError, IntegrityError, InterfaceError, InternalError, OperationalError, ProgrammingError) as e:
            db.session.rollback()
            flash(f"Erro ao Atualizar:{str(e.orig)}", "danger")
        except ValueError as ve:
            db.session.rollback()
            flash(f"Erro ao Atualizar:{ve}", "danger")
    return redirect(url_for('reservas_auditorios.main_page'))