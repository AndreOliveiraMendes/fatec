from typing import Any, Callable, Dict, NotRequired, Tuple, Type, TypedDict

from flask import current_app, request
from sqlalchemy import ColumnElement, and_, select, true
from sqlalchemy.orm import InstrumentedAttribute

from app.extensions import db
from app.models.usuarios import Pessoas, Usuarios, Usuarios_Especiais


class LabelConfig(TypedDict):
    field: InstrumentedAttribute[Any]
    model: NotRequired[Type[Any]]
    join: NotRequired[Any]

class SelectModelConfig(TypedDict):
    model: Type[Any]
    id_field: InstrumentedAttribute[Any]
    label: LabelConfig
    q_filter: Tuple[
        Callable[[Any], ColumnElement[Any]],
        type
    ]
    filters: NotRequired[
        Dict[str, Tuple[Callable[[Any], ColumnElement[Any]], type]]
    ]

def multi_ilike(field, texto):
    palavras = [p for p in texto.split() if len(p) >= 1]

    if not palavras:
        return true()

    return and_(*[
        field.ilike(f"%{p}%")
        for p in palavras
    ])


SELECT_MODELS: Dict[str, SelectModelConfig] = {
    "pessoas": {
        "model": Pessoas,
        "id_field": Pessoas.id_pessoa,
        "label": {
            "field": Pessoas.nome_pessoa
        },
        "q_filter": (lambda n:multi_ilike(Pessoas.nome_pessoa, n), str),
        "filters":{
            "id_pessoa": (lambda i:Pessoas.id_pessoa == i, int),
            "nome_pessoa": (lambda n:multi_ilike(Pessoas.nome_pessoa, n), str)
        }
    },
    "usuarios_especiais": {
        "model": Usuarios_Especiais,
        "id_field": Usuarios_Especiais.id_usuario_especial,
        "label": {
            "field": Usuarios_Especiais.nome_usuario_especial
        },
        "q_filter": (lambda n:multi_ilike(Usuarios_Especiais.nome_usuario_especial, n), str)
    },
    "usuarios": {
        "model": Usuarios,
        "id_field": Usuarios.id_usuario,
        "label": {
            "model": Pessoas,
            "field": Pessoas.nome_pessoa,
            "join": Usuarios.pessoa
        },
        "q_filter": (lambda n:multi_ilike(Pessoas.nome_pessoa, n), str)
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
    label = config.get("label")

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

    sel = select(
        model,
        label["field"].label("label")
    )
    if label and "join" in label:
        sel = sel.join(label["join"])

    if filtro:
        sel = sel.where(*filtro)

    result = db.session.execute(sel).all()
    data = {
        "results": [
            {
                "id": getattr(row[0], id_field.key),
                "text": row.label
            }
            for row in result
        ]
    }

    return data, 200
