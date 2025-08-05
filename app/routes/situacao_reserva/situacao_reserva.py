from copy import copy
from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import datetime
from app.models import db, Turnos, TipoAulaEnum, SituacaoChaveEnum, Situacoes_Das_Reserva
from app.auxiliar.decorators import admin_required
from app.auxiliar.auxiliar_routes import get_user_info, parse_date_string, get_unique_or_500, registrar_log_generico_usuario
from app.auxiliar.dao import get_reservas_por_dia, get_turnos, get_situacoes_por_dia, check_first

bp = Blueprint('situacao_reserva', __name__, url_prefix="/status_reserva")

@bp.route('/')
@admin_required
def gerenciar_status():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    hoje = datetime.today()
    extras = {'hoje':hoje}
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    turno = None

    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    if reserva_turno is not None:
        turno = db.session.get(Turnos, reserva_turno)
    if not reserva_dia:
        reserva_dia = hoje.date()
    reservas_fixas, reservas_temporarias = get_reservas_por_dia(reserva_dia, turno, TipoAulaEnum(reserva_tipo_horario))
    reservas = []
    i, j = 0, 0
    control_1 = len(reservas_fixas) if reservas_fixas else 0
    control_2 = len(reservas_temporarias) if reservas_temporarias else 0
    while i < control_1 or j < control_2:
        reserva = {}
        if i < control_1 and j < control_2:
            rf = reservas_fixas[i]
            rt = reservas_temporarias[j]
            who = check_first(rf, rt)
            if who == 0:
                reserva['horario'] = rf.aulas_ativas
                reserva['laboratorio'] = rf.laboratorios
                reserva['fixa'] = rf
                reserva['temporaria'] = None
                i += 1
            elif who == 1:
                reserva['horario'] = rt.aulas_ativas
                reserva['laboratorio'] = rt.laboratorios
                reserva['fixa'] = None
                reserva['temporaria'] = rt
                j += 1
            else:
                reserva['horario'] = rf.aulas_ativas
                reserva['laboratorio'] = rf.laboratorios
                reserva['fixa'] = rf
                reserva['temporaria'] = rt
                i += 1
                j += 1
        elif i < control_1:
            rf = reservas_fixas[i]
            reserva['horario'] = rf.aulas_ativas
            reserva['laboratorio'] = rf.laboratorios
            reserva['fixa'] = rf
            reserva['temporaria'] = None
            i += 1
        else:
            rt = reservas_temporarias[j]
            reserva['horario'] = rt.aulas_ativas
            reserva['laboratorio'] = rt.laboratorios
            reserva['fixa'] = None
            reserva['temporaria'] = rt
            j += 1
        situacao = get_situacoes_por_dia(reserva['horario'], reserva['laboratorio'], reserva_dia)
        reserva['situacao'] = situacao
        reservas.append(reserva)
    extras['reservas'] = reservas
    extras['situacaoChave'] = SituacaoChaveEnum
    return render_template("status_reserva/status_reserva.html", username=username, perm=perm, **extras)

@bp.route('/atuacionar/<int:aula>/<int:lab>/<data:dia>', methods=['POST'])
@admin_required
def atuacionar(aula, lab, dia):
    userid = session.get('userid')
    chave = request.form.get('situacao')
    situacao = get_unique_or_500(
        Situacoes_Das_Reserva,
        Situacoes_Das_Reserva.id_situacao_aula==aula,
        Situacoes_Das_Reserva.id_situacao_laboratorio==lab,
        Situacoes_Das_Reserva.situacao_dia==dia
    )
    old_data = None
    if situacao:
        old_data = copy(situacao)
    else:
        situacao = Situacoes_Das_Reserva(
            id_situacao_aula=aula,
            id_situacao_laboratorio=lab,
            situacao_dia=dia
        )
    try:
        situacao.situacao_chave = SituacaoChaveEnum(chave)

        db.session.add(situacao)

        db.session.flush()
        registrar_log_generico_usuario(userid, 'Inserção', situacao, old_data, "via menu situacao", True)

        db.session.commit()
        flash("atualizado com sucesso", "success")
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        flash(f"erro ao atualizar:{str(e.orig)}", "danger")
    except ValueError as ve:
        db.session.rollback()
        flash(f"erro ao atualiza:{ve}", "danger")
    return redirect(url_for('situacao_reserva.gerenciar_status'))