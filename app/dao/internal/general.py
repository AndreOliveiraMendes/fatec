from typing import Literal, Type, TypeVar

from flask import abort, current_app, flash
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from app.extensions import Base, db
from app.models.usuarios import Pessoas, Usuarios, Usuarios_Especiais

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

def get_nome_pessoa_by_id(id, tipo = Literal['pessoa', 'usuario', 'usuario_especial'], abort_on_null = True, error_on_empty_id = False):
    if id is None:
        if error_on_empty_id:
            abort(400, description="ID não pode ser vazio.")
        else:
            return ''
    if tipo == 'pessoa':
        obj = db.session.get(Pessoas, id)
        if not obj and abort_on_null:
            abort(404, description="Pessoa não encontrada.")
        return obj.alias or obj.nome_pessoa if obj is not None else ''
    elif tipo == 'usuario':
        obj = db.session.get(Usuarios, id)
        if not obj and abort_on_null:
            abort(404, description="Usuário não encontrado.")
        return obj.pessoa.alias or obj.pessoa.nome_pessoa if obj is not None else ''
    elif tipo == 'usuario_especial':
        obj = db.session.get(Usuarios_Especiais, id)
        if not obj and abort_on_null:
            abort(404, description="Usuário especial não encontrado.")
        return obj.nome_usuario_especial if obj is not None else ''
    else:
        abort(400, description="Tipo inválido para obtenção do nome da pessoa.")

def get_nome_pessoa(obj, abort_on_null = True):
    if not obj:
        if abort_on_null:
            abort(404, description="Registro não encontrado.")
        else:
            return None
    if isinstance(obj, Pessoas):
        return obj.alias or obj.nome_pessoa
    elif isinstance(obj, Usuarios):
        return obj.pessoa.alias or obj.pessoa.nome_pessoa
    elif isinstance(obj, Usuarios_Especiais):
        return obj.nome_usuario_especial
    else:
        abort(400, description="Tipo de objeto inválido para obtenção do nome da pessoa.")