from copy import copy

from flask import abort, flash, redirect, request, session
from flask.typing import ResponseReturnValue

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.general import none_if_empty
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.reservas import check_ownership_or_admin
from app.enums import StatusReservaAuditorioEnum, StatusReservaEquipamentoEnum
from app.extensions import db
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)
from app.models.usuarios import Usuarios
from app.routes.user.handler.handler_base import CHECK_PERIODO_MAP, RESERVA_MAP
from app.service.reservas_services import check_unique_aprovada


def resolve_tipo(tipo_reserva: str):
    data = RESERVA_MAP.get(tipo_reserva)
    if data is None:
        abort(404, description="Tipo de reserva inexistente")
    return data

def editar_reserva_generico(model, id_reserva: int, redirect_url: str) -> ResponseReturnValue:
    userid = session.get('userid')
    reserva = db.get_or_404(model, id_reserva)
    user = db.get_or_404(Usuarios, userid)
    check_ownership_or_admin(reserva)
    check = CHECK_PERIODO_MAP.get(model)
    if check and not check(reserva):
        abort(403, description="Esta reserva não pode mais ser editada fora do período permitido.")
    old_data = copy(reserva)
    if model in [Reservas_Fixas, Reservas_Temporarias]:
        observacao = none_if_empty(request.form.get('observacao'))
        descricao = none_if_empty(request.form.get('descricao'))
        finalidade_reserva = request.form.get('finalidade_reserva', type=int)
        responsavel = none_if_empty(request.form.get('responsavel'))
        responsavel_especial = none_if_empty(request.form.get('responsavel_especial'))
        if user.perm.has(Permission.ADMIN):
            responsavel = reserva.id_responsavel
            responsavel_especial = reserva.id_responsavel_especial
        try:
            reserva.observacoes = observacao
            reserva.descricao = descricao
            reserva.id_finalidade_reserva = finalidade_reserva
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
    elif model == Reservas_Auditorios:
        observacao_responsavel = none_if_empty(request.form.get('Observacao_responsavel'))
        if user.perm.has_any(Permission.ADMIN | Permission.AUTORIZAR):
            responsavel = none_if_empty(request.form.get('responsavel'), int)
            autorizador = none_if_empty(request.form.get('autorizador'), int)
            observacao_autorizador = none_if_empty(request.form.get('Observacao_autorizador'))
            status = none_if_empty(request.form.get('status'))
            has_extra = True
        else:
            has_extra = False

        try:
            reserva.observação_responsavel = observacao_responsavel
            if has_extra:
                if status == "Aprovada":
                    check_unique_aprovada(reserva)
                elif status == "Cancelada":
                    return cancelar_reserva_generico(model, id_reserva, redirect_url)

                reserva.observação_autorizador = observacao_autorizador
                reserva.id_responsavel = responsavel
                reserva.id_autorizador = autorizador
                reserva.status_reserva = StatusReservaAuditorioEnum(status)

            db.session.flush()
            registrar_log_generico_usuario(userid, 'Edição', reserva, old_data, observacao='atraves de listagem')

            db.session.commit()
            flash("sucesso ao editar reserva", "success")
        except DB_ERRORS as e:
            handle_db_error(e, "Erro ao editar reserva")
        except ValueError as e:
            handle_db_error(e, "Erro ao editar reserva")
    elif model == Reservas_Equipamentos:      
        if user.perm.has(Permission.ADMIN):
            responsavel = request.form.get('responsavel')
            status = request.form.get('status')

            try:
                reserva.id_responsavel = responsavel
                new_status = StatusReservaEquipamentoEnum(status)
                if new_status == StatusReservaEquipamentoEnum.CANCELADA:
                    return cancelar_reserva_generico(model, id_reserva, redirect_url)
                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', reserva, old_data, observacao='atraves de listagem')

                db.session.commit()
                flash("sucesso ao editar reserva", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar reserva")
            except ValueError as e:
                handle_db_error(e, "Erro ao editar reserva")
        else:
            flash("sem permissão para editar")
    else:
        flash("Tipo de reserva não editável ou inexistente ou metodo não implementado", "danger")
    return redirect(redirect_url)

def cancelar_reserva_generico(model, id_reserva, redirect_url):
    userid = session.get('userid')
    reserva = db.get_or_404(model, id_reserva)
    user = db.get_or_404(Usuarios, userid)
    check_ownership_or_admin(reserva)
    check = CHECK_PERIODO_MAP.get(model)
    if check and not check(reserva):
        abort(403, description="Esta reserva não pode mais ser cancelada fora do período permitido.")
    if model in [Reservas_Equipamentos, Reservas_Auditorios]:
        cancelou = False
        if model == Reservas_Equipamentos and \
            (reserva.status_reserva == StatusReservaEquipamentoEnum.PENDENTE or user.perm.has(Permission.ADMIN)):
            motivo_cancelamento = request.form.get('motivo_cancelamento')
            reserva.status_reserva = StatusReservaEquipamentoEnum.CANCELADA
            reserva.motivo_cancelamento = motivo_cancelamento
            reserva.cancelado_por_id = userid
            cancelou = True
        elif model == Reservas_Auditorios and \
            (reserva.status_reserva == StatusReservaAuditorioEnum.AGUARDANDO or user.perm.has(Permission.ADMIN)):
            reserva.status_reserva = StatusReservaAuditorioEnum.CANCELADA
            cancelou = True
        if cancelou:
            try:
                db.session.flush()
                registrar_log_generico_usuario(userid, 'Edição', reserva, observacao="cancelamento atraves da listagem")
                db.session.commit()
                flash("Reserva cancelada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao cancelar reserva")
        else:
            flash("Erro ao cancelar reserva", "danger")
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