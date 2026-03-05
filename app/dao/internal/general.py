
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

    if "foreign key" in raw:
        return "Registro relacionado não encontrado."

    if "cannot be null" in raw or "not null constraint" in raw:
        return "Campo obrigatório não preenchido."

    if "data too long" in raw:
        return "Valor maior que o permitido."

    return "Erro ao salvar dados."

def handle_db_error(e, msg):
    db.session.rollback()

    user_msg = _friendly_db_message(e)

    flash(f"{msg}: {user_msg}", "danger")

    current_app.logger.error("%s | erro=%s", msg, e)

