from flask import abort, current_app
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import and_, func, select

from app.extensions import db
from app.models.aulas import Aulas, Aulas_Ativas
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)

RESERVA_MAP = {
    "fixa": {
        "model": Reservas_Fixas,
        "order": Reservas_Fixas.id_reserva_semestre
    },
    "temporaria": {
        "model": Reservas_Temporarias,
        "order": Reservas_Temporarias.inicio_reserva
    }
}

FILTERS = {
    "fixa": {
        "semestre": (lambda s:Reservas_Fixas.id_reserva_semestre == s, int),
        "lab": (lambda l:Reservas_Fixas.id_reserva_local == l, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "obs": (
            lambda _: and_(
                Reservas_Fixas.observacoes.isnot(None),
                func.trim(Reservas_Fixas.observacoes) != ''
            ),
            bool
        )
    },
    "temporaria": {
        "data_inicio": (lambda d:Reservas_Temporarias.inicio_reserva >= d, str),
        "data_fim": (lambda d:Reservas_Temporarias.fim_reserva <= d, str),
        "lab": (lambda l:Reservas_Temporarias.id_reserva_local == l, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "obs": (
            lambda _: and_(
                Reservas_Temporarias.observacoes.isnot(None),
                func.trim(Reservas_Temporarias.observacoes) != ''
            ),
            bool
        )
    }
}

def get_reservas(params, page, tipo):
    base = RESERVA_MAP.get(tipo, {})
    if not base:
        abort(404, description="Tipo invalido")
    model = base.get('model')
    org_column = base.get('order')
    if not model:
        abort(404, description="Usuário não encontrado.")
    filtro = []
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
        page=page, per_page=50, error_out=False
    )
    return pagination