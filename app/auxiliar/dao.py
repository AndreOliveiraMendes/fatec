
from typing import Type, TypeVar

from flask import abort, current_app, flash
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from app.auxiliar.auxiliar_dao import _friendly_db_message
from app.extensions import db, Base

T = TypeVar("T", bound=Base)

def get_unique_or_500(model: Type[T], *args, **kwargs):
    try:
        return db.session.execute(
            select(model).where(*args, **kwargs)
        ).scalar_one_or_none()
    except MultipleResultsFound:
        abort(500, description=f"Erro ao consultar {model.__name__}.")

def _handle_db_error(e, msg):
    db.session.rollback()

    user_msg = _friendly_db_message(e)

    flash(f"{msg}: {user_msg}", "danger")

    current_app.logger.error("%s | erro=%s", msg, e)

