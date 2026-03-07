from flask import abort
from sqlalchemy import and_, func, or_, select

from app.auxiliar.constant import IntervalConflictError
from app.extensions import db
from app.models.aulas import Aulas_Ativas, Semestres, Turnos


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
        raise IntervalConflictError(
            "Já existe uma aula ativa que conflita com o período informado.",
            table="aulas_ativas",
            fields=("id_aula", "id_semana", "tipo_aula"),
            values=(aula, semana, tipo),
            interval=(inicio, fim)
        )

def check_turno(inicio, fim, id = None):
    base_filter = [
        and_(
            Turnos.horario_inicio <= fim,
            Turnos.horario_fim >= inicio
        )
    ]
    
    if id is not None:
        base_filter.append(Turnos.id_turno != id)
        
    sel = select(func.count()).select_from(Turnos).where(*base_filter)
    res = db.session.scalar(sel)
    
    if res is None:
        abort(500, description="Erro ao verificar conflito de turno.")
        
    if res > 0:
        raise IntervalConflictError(
            "Já existe um turno que conflita com o intervalo informado.",
            table="turnos",
            interval=(inicio, fim)
        )
        
def check_semestre(inicio, fim, id=None):
    base_filter = [
        and_(
            Semestres.data_inicio <= fim,
            Semestres.data_fim >= inicio
        )
    ]

    if id is not None:
        base_filter.append(Semestres.id_semestre != id)

    sel = select(func.count()).select_from(Semestres).where(*base_filter)
    res = db.session.scalar(sel)
    
    if res is None:
        abort(500, description="Erro ao verificar conflito de semestres.")

    if res > 0:
        raise IntervalConflictError(
            "Já existe um semestre que conflita com o período informado.",
            table="semestres",
            interval=(inicio, fim)
        )