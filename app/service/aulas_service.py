from sqlalchemy import and_, or_, select, func
from sqlalchemy.exc import IntegrityError
from flask import abort

from app.extensions import db
from app.models.aulas import Aulas_Ativas


def check_aula_ativa(inicio, fim, aula, semana, tipo, id=None):
    base_filter = [
        Aulas_Ativas.id_aula == aula,
        Aulas_Ativas.id_semana == semana,
        Aulas_Ativas.tipo_aula == tipo
    ]

    if id is not None:
        base_filter.append(Aulas_Ativas.id_aula_ativa != id)

    if inicio and fim:
        base_filter.append(
            and_(
                or_(Aulas_Ativas.fim_ativacao.is_(None), Aulas_Ativas.fim_ativacao >= inicio),
                or_(Aulas_Ativas.inicio_ativacao.is_(None), Aulas_Ativas.inicio_ativacao <= fim)
            )
        )
    elif inicio and not fim:
        base_filter.append(
            or_(Aulas_Ativas.fim_ativacao.is_(None), Aulas_Ativas.fim_ativacao >= inicio)
        )
    elif not inicio and fim:
        base_filter.append(
            or_(Aulas_Ativas.inicio_ativacao.is_(None), Aulas_Ativas.inicio_ativacao <= fim)
        )

    sel = select(func.count()).select_from(Aulas_Ativas).where(*base_filter)
    res = db.session.scalar(sel)

    if res is None:
        abort(500, description="Erro ao verificar conflito de aula ativa.")

    if res > 0:
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("Já existe uma aula ativa com os mesmos dados.")
        )
