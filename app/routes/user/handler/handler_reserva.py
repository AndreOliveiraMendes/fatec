from copy import copy

from flask import abort, flash, redirect, request, session
from flask.typing import ResponseReturnValue

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.general import none_if_empty
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.reservas import check_ownership_or_admin
from app.enums import FinalidadeReservaEnum, StatusReservaEquipamentoEnum
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos
from app.models.reservas.reservas_laboratorios import Reservas_Fixas, Reservas_Temporarias
from app.models.usuarios import Permissoes
from app.routes.user.handler.handler_base import CHECK_PERIODO_MAP, RESERVA_MAP


def resolve_tipo(tipo_reserva: str):
    data = RESERVA_MAP.get(tipo_reserva)
    if data is None:
        abort(404, description="Tipo de reserva inexistente")
    return data

def cancelar_reserva_generico(model, id_reserva, redirect_url):
    userid = session.get('userid')
    reserva = db.get_or_404(model, id_reserva)
    check_ownership_or_admin(reserva)
    check = CHECK_PERIODO_MAP.get(model)
    if check and not check(reserva):
        abort(403, description="Esta reserva não pode mais ser cancelada fora do período permitido.")
    if model == Reservas_Equipamentos:
        if reserva.estado == StatusReservaEquipamentoEnum.PENDENTE:
            reserva.estado = StatusReservaEquipamentoEnum.CANCELADA
            try:
                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', reserva, observacao="cancelamento atraves da listagem")
                db.session.commit()
                flash("Reserva cancelada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cancelar reserva")
        else:
            flash("somente reservas pendentes podem ser canceladas", "danger")
    else:
        try:
            db.session.delete(reserva)
            db.session.flush()
            registrar_log_generico_usuario(userid, 'Exclusão', reserva, observacao="atraves da listagem")
            db.session.commit()
            flash("Reserva cancelada com sucesso", "success")
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao excluir reserva")
    return redirect(redirect_url)

def editar_reserva_generico(model, id_reserva: int, redirect_url: str) -> ResponseReturnValue:
    userid = session.get('userid')
    reserva = db.get_or_404(model, id_reserva)
    check_ownership_or_admin(reserva)
    check = CHECK_PERIODO_MAP.get(model)
    if check and not check(reserva):
        abort(403, description="Esta reserva não pode mais ser editada fora do período permitido.")
    if model in [Reservas_Fixas, Reservas_Temporarias]:
        observacao = none_if_empty(request.form.get('observacao'))
        finalidade_reserva = request.form.get('finalidade_reserva')
        if not finalidade_reserva:
            finalidade_reserva = FinalidadeReservaEnum.GRADUACAO.value
        responsavel = none_if_empty(request.form.get('responsavel'))
        responsavel_especial = none_if_empty(request.form.get('responsavel_especial'))
        perm = db.session.get(Permissoes, userid)
        if not perm or perm.permissao&Permission.ADMIN == 0:
            responsavel = reserva.id_responsavel
            responsavel_especial = reserva.id_responsavel_especial
        try:
            old_data = copy(reserva)
            reserva.observacoes = observacao
            reserva.finalidade_reserva = FinalidadeReservaEnum(finalidade_reserva)
            reserva.id_responsavel = responsavel
            reserva.id_responsavel_especial = responsavel_especial

            db.session.flush()
            registrar_log_generico_usuario(userid, 'Edição', reserva, old_data, observacao='atraves de listagem')

            db.session.commit()
            flash("sucesso ao editar reserva", "success")
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao editar reserva")
        except ValueError as e:
            handle_db_error(e, "Erro ao editar reserva")
    else:
        flash("Tipo de reserva não editável ou inexistente ou metodo não implementado", "danger")
    return redirect(redirect_url)