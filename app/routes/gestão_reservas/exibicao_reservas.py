from copy import copy
from datetime import datetime
from typing import Any

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.aulas import get_turno_by_time, get_turnos
from app.dao.internal.controle import get_exibicao_por_dia
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.reservas import get_reservas_por_dia
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.enums import TipoAulaEnum, TipoReservaEnum
from app.extensions import db
from app.models.aulas import Aulas_Ativas, Turnos
from app.models.controle import Exibicao_Reservas
from app.models.locais import Locais

from .handler import process_reservas

bp = Blueprint('exibicao_reserva', __name__, url_prefix="/gestao_reservas")

@bp.route('/exibicao', methods=['GET'])
@admin_required
def gerenciar_exibicao():
    userid = session.get('userid')
    user = get_user(userid)
    hoje = datetime.today()
    extras: dict[str, Any] = {'hoje':hoje}
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
    extras['reservas'] = process_reservas(reservas_fixas, reservas_temporarias, reserva_dia)
    icons = [
        ["glyphicon-th-list", "warning", "temporaria priorizada"],
        ["glyphicon-lock", "info", "fixa"],
        ["glyphicon-time", "success", "temporaria"]
    ]
    extras['icons'] = icons
    return render_template("gestão_reservas/reservas_laboratorios/exibicao_reserva.html", user=user, **extras)

@bp.route('/exibicao/<int:id_aula>/<int:id_lab>/<data:dia>', methods=['POST'])
@admin_required
def atualizar_exibicao(id_aula, id_lab, dia):
    userid = session.get('userid')
    aula = db.get_or_404(Aulas_Ativas, id_aula)
    lab = db.get_or_404(Locais, id_lab)

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
                    id_exibicao_local=id_lab,
                    exibicao_dia=dia
                )
            exibicao.tipo_reserva = TipoReservaEnum(new_exibicao_config)

            db.session.add(exibicao)

            db.session.flush()
            registrar_log_generico_usuario(userid, acao, exibicao, old_exibicao, 'pelo painel', True)

            db.session.commit()
            flash("dados atualizados com sucesso", "success")
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao atualizar dados")
        except ValueError as e:
            handle_db_error(e, "Erro ao atualizar dados")
    else:
        if exibicao:
            try:
                db.session.delete(exibicao)

                db.session.flush()
                registrar_log_generico_usuario(userid, 'Exclusão', exibicao, observacao='pelo painel')

                db.session.commit()
                flash("dados atualizados com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao atualizar dados")
            except ValueError as e:
                handle_db_error(e, "Erro ao atualizar dados")

    return redirect(url_for("exibicao_reserva.gerenciar_exibicao"))