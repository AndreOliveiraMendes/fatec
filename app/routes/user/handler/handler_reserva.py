from copy import copy

from flask import abort, flash, redirect, request, session
from flask.typing import ResponseReturnValue

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.general import none_if_empty
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.reservas import (check_ownership_or_admin,
                                       check_periodo_fixa)
from app.enums import FinalidadeReservaEnum
from app.extensions import db
from app.models.reservas.reservas_laboratorios import Reservas_Fixas
from app.models.usuarios import Permissoes
from app.routes.user.handler.handler_base import RESERVA_MAP


def resolve_tipo(tipo_reserva: str):
    data = RESERVA_MAP.get(tipo_reserva)
    if data is None:
        abort(404, description="Tipo de reserva inexistente")
    return data

def cancelar_reserva_generico(modelo, id_reserva, redirect_url):
    userid = session.get('userid')
    reserva = db.get_or_404(modelo, id_reserva)
    check_ownership_or_admin(reserva)
    if modelo == Reservas_Fixas and not check_periodo_fixa(reserva):
        abort(403, description="periodo de cadastro expirado ou ainda não começado")
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
    if model == Reservas_Fixas and not check_periodo_fixa(reserva):
        abort(403, description="Esta reserva não pode mais ser alterada fora do período permitido.")
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
    return redirect(redirect_url)