from flask import abort, current_app
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import Permission
from app.extensions import db
from app.models.aulas import Aulas, Aulas_Ativas
from app.models.usuarios import Usuarios
from app.routes.user.handler.handler_base import FILTERS, RESERVA_MAP


def get_reservas_auditorios(userid, args_extras, page):
    user = db.session.get(Usuarios, userid)
    base = RESERVA_MAP.get('auditorios', {})
    if not base:
        abort(404, description="Tipo invalido")
    model = base.get('model')
    org_column = base.get('order')
    if not user or not model:
        abort(404, description="Usuário não encontrado ou modelo inválido.")
    filtro = []
    if not user.perm.has(Permission.ADMIN):
        filtro.append(model.id_responsavel == user.id_pessoa)
    for key, (condition, cast) in FILTERS.get('auditorios', {}).items():
        raw = args_extras.get(key)
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