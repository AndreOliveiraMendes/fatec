from copy import copy
from datetime import datetime
from typing import Literal

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)
from sqlalchemy import func, select
from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

from app.auxiliar.auxiliar_routes import (get_user_info, parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.constant import PERM_ADMIN, PERM_AUTORIZAR
from app.auxiliar.dao import (get_auditorios, get_aulas_ativas_por_dia,
                              get_reservas_auditorios)
from app.auxiliar.decorators import reserva_auditorio_required
from app.models import (Aulas, Aulas_Ativas, Dias_da_Semana,
                        Reservas_Auditorios, StatusReservaAuditorioEnum,
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
    auditorios = get_auditorios()
    if len(auditorios) == 0:
        flash("sem auditorio cadastrado ou ativo", "danger")
        return redirect(url_for('default.home'))
    extras['auditorios'] = auditorios

    reserva_dia = parse_date_string(request.args.get('reserva-dia'))
    if not 'reserva-dia' in request.args:
        reserva_dia = today.date()
    extras['reserva_dia'] = reserva_dia

    conditions = []
    if reserva_dia:
        conditions.append(Reservas_Auditorios.dia_reserva == reserva_dia)
    extras['reservas_auditorios'] = get_reservas_auditorios(user.pessoa.id_pessoa, user.perm&(PERM_ADMIN+PERM_AUTORIZAR), *conditions)
    return render_template('reserva_auditorio/main.html', user=user, **extras)

def check_own_reserva(reserva:Reservas_Auditorios, user:Usuarios):
    if user.id_pessoa != reserva.id_responsavel and user.perm & (PERM_ADMIN+PERM_AUTORIZAR) == 0:
        abort(403)

def check_role(user:Usuarios, action:Literal['CR', 'AR']):
    if action == 'CR' and user.perm & PERM_ADMIN == 0:
        abort(403)
    elif action == 'AR' and user.perm & (PERM_ADMIN+PERM_AUTORIZAR) == 0:
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


@bp.route('/atualizar_status_reserva/<int:id_reserva>', methods=['POST'])
@reserva_auditorio_required
def atualizar_status(id_reserva):
    """
    ("Aguardando", "Cancelada") -> ("Aguardando", "Cancelada")
    ("Aguardando", "Aprovada", "Reprovada") -> ("Aprovada", "Reprovada")
    """
    userid = session.get('userid')
    user = get_user_info(userid)
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    check_own_reserva(reserva, user)
    old_reserva = copy(reserva)
    old_status = reserva.status_reserva.value
    new_status = request.form.get('status')
    if old_status in ['Cancelada', 'Aguardando'] and new_status in ['Cancelada', 'Aguardando']:
        check_role(user, "CR")
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
        check_role(user, "AR")
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

@bp.route('/get_info/<int:id_reserva>')
@reserva_auditorio_required
def get_info_reserva(id_reserva):
    userid = session.get('userid')
    user = get_user_info(userid)
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    check_own_reserva(reserva, user)
    return {
        "local":reserva.local.nome_local,
        "dia":reserva.dia_reserva,
        "horario": f"{reserva.aula_ativa.aula.horario_inicio:%H:%M} às {reserva.aula_ativa.aula.horario_fim:%H:%M}",
        "observacao_responsavel": reserva.observação_responsavel,
        "observacao_autorizador": reserva.observação_autorizador,
        "status": reserva.status_reserva.value,
        "responsavel": reserva.responsavel.nome_pessoa,
        "autorizador": reserva.autorizador.nome_pessoa if reserva.autorizador else None,
        "comentario_responsavel": url_for('reservas_auditorios.editar_observacao', field='responsavel', id_reserva=id_reserva),
        "comentario_autorizador": url_for('reservas_auditorios.editar_observacao', field='autorizador', id_reserva=id_reserva),
    }

@bp.route('/editar/<field>/<int:id_reserva>', methods=['POST'])
@reserva_auditorio_required
def editar_observacao(field, id_reserva):
    userid = session.get('userid')
    user = get_user_info(userid)
    reserva = db.get_or_404(Reservas_Auditorios, id_reserva)
    check_own_reserva(reserva, user)
    observacao = request.form.get('observacao')
    old_reserva = copy(reserva)
    try:
        if field == 'responsavel':
            reserva.observação_responsavel = observacao
        elif field == 'autorizador':
            reserva.observação_autorizador = observacao

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Edição', reserva, old_reserva, 'comentario', True)

        db.session.commit()
        flash(f"Comentario {field} realizado com sucesso", "success")
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        flash(f"Erro ao comentar:{str(e.orig)}", "danger")
    return redirect(url_for('reservas_auditorios.main_page'))

@bp.route('/api/times', methods=['GET'])
def get_times():
    dia = parse_date_string(request.args.get('dia'))
    if not dia:
        abort(500)
    aulas_ativas = get_aulas_ativas_por_dia(dia)
    result = []
    for aula_ativa, aula, dia_semana in aulas_ativas:
        result.append({
            'id_aula_ativa': aula_ativa.id_aula_ativa,
            'horario_inicio': aula.horario_inicio.strftime('%H:%M'),
            'horario_fim': aula.horario_fim.strftime('%H:%M'),
            'nome_semana': dia_semana.nome_semana
        })
    return result

@bp.route('/adicionando_reserva_auditorio', methods=['POST'])
@reserva_auditorio_required
def adicionar():
    userid = session.get('userid')
    user = get_user_info(userid)
    auditorio = request.form.get('auditorio')
    dia = parse_date_string(request.form.get('dia'))
    hora = request.form.get('hora')
    observacao = request.form.get('observacao')
    try:
        nova_reserva = Reservas_Auditorios()
        nova_reserva.id_reserva_local = auditorio
        nova_reserva.id_reserva_aula = hora
        nova_reserva.dia_reserva = dia
        nova_reserva.id_responsavel = user.id_pessoa
        if observacao:
            nova_reserva.observação_responsavel = observacao

        db.session.add(nova_reserva)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Inserção', nova_reserva, observacao='atraves da tela de reserva')

        db.session.commit()
        flash("reserva adicionada com sucesso", "success")
    except (DataError, IntegrityError, InterfaceError,
        InternalError, OperationalError, ProgrammingError) as e:
        db.session.rollback()
        flash(f"Erro ao adicionar:{str(e.orig)}", "danger")
    return redirect(url_for('reservas_auditorios.main_page'))
