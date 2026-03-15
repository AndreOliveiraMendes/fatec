from typing import Any, Callable, Literal

from flask import flash, g

from app.auxiliar.constant import DB_ERRORS
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.extensions import db


def db_action(
    action_type: Literal["Inserção", "Edição", "Exclusão"],
    success_msg: str,
    error_msg: str,
    obj=None,
    old_obj=None,
    action: Callable[..., Any] | None = None,
    post_action: Callable[..., Any] | None = None,
    observacao: str | None=None
) -> None:
    try:
        if action:
            action()
        if action_type in ("Inserção", "Edição") and obj:
            db.session.add(obj)
        elif action_type == "Exclusão" and obj:
            db.session.delete(obj)

        db.session.flush()
        
        if post_action:
            post_action()

        if obj is not None:
            registrar_log_generico_usuario(
                g.userid, action_type, obj, old_obj, observacao
            )

        db.session.commit()
        flash(success_msg, "success")

    except DB_ERRORS as e:
        handle_db_error(e, error_msg)
    except ValueError as e:
        handle_db_error(e, error_msg)