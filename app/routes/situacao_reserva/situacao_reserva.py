from copy import copy
from datetime import datetime

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auxiliar.auxiliar_routes import (get_unique_or_500, get_user_info,
                                          parse_date_string,
                                          registrar_log_generico_usuario)
from app.auxiliar.dao import (check_first, get_exibicao_por_dia,
                              get_reservas_por_dia, get_situacoes_por_dia,
                              get_turno_by_time, get_turnos)
from app.auxiliar.decorators import admin_required
from app.models import (Aulas_Ativas, Exibicao_Reservas, Laboratorios,
                        SituacaoChaveEnum, Situacoes_Das_Reserva, TipoAulaEnum,
                        TipoReservaEnum, Turnos, db)

bp = Blueprint('situacao_reserva', __name__, url_prefix="/status_reserva")

@bp.route('/exibicao', methods=['GET'])
@admin_required
def gerenciar_exibicao():
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    hoje = datetime.today()
    extras = {'hoje':hoje}
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if reserva_turno:
            reserva_turno = reserva_turno.id_turno
    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    turno = None

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
        reserva['exibicao'] = get_exibicao_por_dia(reserva['horario'], reserva['laboratorio'], reserva_dia)
        reservas.append(reserva)
    extras['reservas'] = reservas
    icons = [
        ["glyphicon-th-list", "warning", "temporaria priorizada"],
        ["glyphicon-lock", "info", "fixa"],
        ["glyphicon-time", "success", "temporaria"]
    ]
    extras['icons'] = icons
    return render_template("status_reserva/exibicao_reserva.html", username=username, perm=perm, **extras)

@bp.route('/exibicao/<int:id_aula>/<int:id_lab>/<data:dia>', methods=['POST'])
@admin_required
def atualizar_exibicao(id_aula, id_lab, dia):
    userid = session.get('userid')
    aula = db.get_or_404(Aulas_Ativas, id_aula)
    lab = db.get_or_404(Laboratorios, id_lab)

    new_exibicao_config = request.form.get('exibicao')
    exibicao = get_exibicao_por_dia(aula, lab, dia)
    old_exibicao = None
    if new_exibicao_config in ['fixa', 'temporaria']:
        try:
            acao = 'Inserção'
            if exibicao:
                old_exibicao = copy(exibicao)
                acao = 'Edição'
            else:
                exibicao = Exibicao_Reservas(
                    id_exibicao_aula=id_aula,
                    id_exibicao_laboratorio=id_lab,
                    exibicao_dia=dia
                )
            exibicao.tipo_reserva = TipoReservaEnum(new_exibicao_config)

            db.session.add(exibicao)

            db.session.flush()
            registrar_log_generico_usuario(userid, acao, exibicao, old_exibicao, 'pelo painel', True)

            db.session.commit()
            flash("dados atualizados com sucesso", "success")
        except (IntegrityError, OperationalError) as e:
            db.session.rollback()
            flash(f"Erro ao atualizar dados:{str(e.orig)}", "danger")
        except ValueError as ve:
            db.session.rollback()
            flash(f"Erro ao atualizar dados:{ve}", "danger")
    else:
        if exibicao:
            try:
                db.session.delete(exibicao)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', exibicao, observacao='pelo painel')

                db.session.commit()
                flash("dados atualizados com sucesso", "success")
            except (IntegrityError, OperationalError) as e:
                db.session.rollback()
                flash(f"Erro ao atualizar dados:{str(e.orig)}", "danger")
            except ValueError as ve:
                db.session.rollback()
                flash(f"Erro ao atualizar dados:{ve}", "danger")

    return redirect(url_for("situacao_reserva.gerenciar_exibicao"))

@bp.route('/<tipo_reserva>')
def gerenciar_situacoes(tipo_reserva):
    icons = [
        ["glyphicon-thumbs-down", "danger", "Não pegou a chave"],
        ["glyphicon-thumbs-up", "success", "Pegou a chave"],
        ["glyphicon-ok", "info", "Reserva concluida"] 
    ]
    hoje = datetime.today()
    extras = {'hoje':hoje}
    extras['icons'] = icons
    reserva_dia = parse_date_string(request.args.get('reserva-dia', default=hoje.date().strftime("%Y-%m-%d")))
    reserva_turno = request.args.get('reserva_turno', type=int)
    reserva_tipo_horario = request.args.get('reserva_tipo_horario', default=TipoAulaEnum.AULA.value)
    if not 'reserva_turno' in request.args:
        reserva_turno = get_turno_by_time(hoje.time())
        if reserva_turno:
            reserva_turno = reserva_turno.id_turno
    if not reserva_tipo_horario:
        reserva_tipo_horario = TipoAulaEnum.AULA.value
    extras['turnos'] = get_turnos()
    extras['tipo_aula'] = TipoAulaEnum
    extras['reserva_dia'] = reserva_dia
    extras['reserva_turno'] = reserva_turno
    extras['reserva_tipo_horario'] = reserva_tipo_horario
    if tipo_reserva == 'fixa':
        return gerenciar_situacoes_reservas_fixas(extras)
    elif tipo_reserva == 'temporaria':
        return gerenciar_situacoes_reservas_temporarias(extras)

def gerenciar_situacoes_reservas_fixas(extras):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    turno = db.session.get(Turnos, extras['reserva_turno']) if extras['reserva_turno'] else None
    reservas_fixas = get_reservas_por_dia(
        extras['reserva_dia'], turno, TipoAulaEnum(extras['reserva_tipo_horario']),
        'fixa'
    )
    extras['reservas'] = reservas_fixas
    return render_template("status_reserva/status_fixas.html", username=username, perm=perm, **extras)

def gerenciar_situacoes_reservas_temporarias(extras):
    userid = session.get('userid')
    username, perm = get_user_info(userid)
    return render_template("status_reserva/status_temporarias.html", username=username, perm=perm, **extras)