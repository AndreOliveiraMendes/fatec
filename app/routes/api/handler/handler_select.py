from typing import Any, Callable, Dict, Tuple, Type, TypedDict

from flask import current_app, request
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.sql.elements import ColumnElement

from app.extensions import db
from app.models.usuarios import Pessoas, Usuarios_Especiais


class SelectModelConfig(TypedDict):
    model: Type[DeclarativeMeta]
    id_field: ColumnElement
    label_field: ColumnElement

    q_filter: Tuple[Callable[[Any], Any], type]

    filters: Dict[str, Tuple[Callable[[Any], Any], type]]

SELECT_MODELS: Dict[str, SelectModelConfig] = {
    "pessoas": {
        "model": Pessoas,
        "id_field": Pessoas.id_pessoa,
        "label_field": Pessoas.nome_pessoa,
        "q_filter": (lambda n:Pessoas.nome_pessoa.ilike(f"%{n}%"), str),
        "filters":{
            "id_pessoa": (lambda i:Pessoas.id_pessoa == i, int),
            "nome_pessoa": (lambda n:Pessoas.nome_pessoa.ilike(f"%{n}%"), str)
        }
    },
    "usuarios_especiais": {
        "model": Usuarios_Especiais,
        "id_field": Usuarios_Especiais.id_usuario_especial,
        "label_field": Usuarios_Especiais.nome_usuario_especial,
        "q_filter": (lambda n:Usuarios_Especiais.nome_usuario_especial.ilike(f"%{n}%"), str)
    }
}

def get_results(entity, q):
    config = SELECT_MODELS.get(entity)

    if not config:
        return {"error": "Entidade inválida"}, 400
    
    model = config.get("model")
    q_filters = config.get("q_filter")
    filters = config.get("filters", {})
    id_field = config.get("id_field")
    label_field = config.get("label_field")

    filtro = []
    condition, cast = q_filters
    if q:
        try:
            filtro.append(condition(cast(q)))
        except (TypeError, ValueError) as e:
            current_app.logger.warning("erro ao aplicar condição [label]")
            return {"error": "condição invalida"}, 400
    if filters:
        for key, (condition, cast) in filters.items():
            raw = request.args.get(key)
            if raw:
                try:
                    filtro.append(condition(cast(raw)))
                except (TypeError, ValueError) as e:
                    current_app.logger.warning("erro ao aplicar condição [filters]")
                    return {"error": "condição invalida"}, 400

    sel = select(model).order_by(label_field)
    if filtro:
        sel = sel.where(*filtro)

    result = db.session.execute(sel).scalars().all()

    return {
        "results":[
            {
                "id": getattr(obj, id_field.key),
                "text": getattr(obj, label_field.key)
            }
            for obj in result
        ]
    }, 200
