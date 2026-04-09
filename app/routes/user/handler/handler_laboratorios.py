from copy import copy

from flask import (abort, current_app, flash, redirect, request, session,
                   url_for)
from flask.typing import ResponseReturnValue
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, select

from app.auxiliar.constant import DB_ERRORS, Permission
from app.auxiliar.general import none_if_empty
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.reservas import (check_ownership_or_admin,
                                       check_periodo_fixa, info_reserva_fixa,
                                       info_reserva_temporaria)
from app.enums import FinalidadeReservaEnum
from app.extensions import db
from app.models.aulas import Aulas, Aulas_Ativas
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)
from app.models.usuarios import Permissoes, Usuarios

RESERVA_MAP = {
    "fixa": {
        "model": Reservas_Fixas,
        "order": Reservas_Fixas.id_reserva_semestre,
        "info": info_reserva_fixa,
        "redirect": lambda: url_for('usuario_reservas_laboratorios.gerenciar_reserva_fixa')
    },
    "temporaria": {
        "model": Reservas_Temporarias,
        "order": Reservas_Temporarias.inicio_reserva,
        "info": info_reserva_temporaria,
        "redirect": lambda: url_for('usuario_reservas_laboratorios.gerenciar_reserva_temporaria')
    }
}

FILTERS = {
    "fixa": {
        "semestre": (lambda s:Reservas_Fixas.id_reserva_semestre == s, int),
        "responsavel": (lambda r:Reservas_Fixas.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Fixas.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Fixas.id_reserva_local == l, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "finalidade": (lambda f:Reservas_Fixas.finalidade_reserva == FinalidadeReservaEnum(f), str)
    },
    "temporaria": {
        "responsavel": (lambda r:Reservas_Temporarias.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Temporarias.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Temporarias.id_reserva_local == l, int),
        "dia": (lambda d:and_(Reservas_Temporarias.inicio_reserva <= d, Reservas_Temporarias.fim_reserva >= d), str),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "finalidade": (lambda f:Reservas_Temporarias.finalidade_reserva == FinalidadeReservaEnum(f), str)
    }
}

def resolve_tipo(tipo_reserva: str):
    data = RESERVA_MAP.get(tipo_reserva)
    if data is None:
        abort(404, description="Tipo de reserva inexistente")
    return data

def get_reservas(userid, params, page, tipo):
    user = db.session.get(Usuarios, userid)
    base = RESERVA_MAP.get(tipo, {})
    if not base:
        abort(404, description="Tipo invalido")
    model = base.get('model')
    org_column = base.get('order')
    if not user or not model:
        abort(404, description="Usuário não encontrado.")
    filtro = []
    if not user.perm.has(Permission.ADMIN):
        filtro.append(model.id_responsavel == user.id_pessoa)
    for key, (condition, cast) in FILTERS.get(tipo, {}).items():
        raw = params.get(key)
        if raw:
            try:
                filtro.append(condition(cast(raw)))
            except (TypeError, ValueError) as e:
                current_app.logger.warning(f"Filtro inválido {key}={raw}")

    sel_reservas = select(model).join(Aulas_Ativas).join(Aulas).where(*filtro).order_by(
        org_column,
        Aulas_Ativas.id_semana,
        Aulas.horario_inicio
    )
    pagination = SelectPagination(select=sel_reservas, session=db.session,
        page=page, per_page=5, error_out=False
    )
    return pagination

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