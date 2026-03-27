from typing import Type, TypeVar

from flask import abort, current_app, flash
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from app.extensions import Base, db

T = TypeVar("T", bound=Base)

def get_unique_or_500(model: Type[T], *args, **kwargs):
    try:
        return db.session.execute(
            select(model).where(*args, **kwargs)
        ).scalar_one_or_none()
    except MultipleResultsFound:
        abort(500, description=f"Erro ao consultar {model.__name__}.")
        
def _friendly_db_message(error):
    raw = str(getattr(error, "orig", error)).lower()

    if "duplicate entry" in raw or "unique constraint" in raw:
        return "Registro já existe."

    if "cannot delete or update a parent row" in raw:
        return "Registro não pode ser excluído pois está sendo utilizado."

    if "cannot add or update a child row" in raw:
        return "Registro relacionado não encontrado."

    if "cannot be null" in raw or "not null constraint" in raw:
        return "Campo obrigatório não preenchido."

    if "data too long" in raw:
        return "Valor maior que o permitido."

    if "check constraint" in raw:
        return "Valor inválido para os campos informados."

    return "Não foi possível concluir a operação."

def handle_db_error(e, msg, show_flash_message=True):
    db.session.rollback()

    if show_flash_message:
        user_msg = _friendly_db_message(e)
        flash(f"{msg}: {user_msg}", "danger")

    current_app.logger.error("%s | erro=%s", msg, e)

