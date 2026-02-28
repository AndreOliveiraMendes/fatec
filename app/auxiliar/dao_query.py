from datetime import date
from typing import Type

from sqlalchemy import ColumnElement, and_, between, case, desc, or_

from app.models.aulas import Aulas, Aulas_Ativas, Turnos
from app.models.reservas.reservas_laboratorios import ReservaBase
from config.general import FIRST_DAY_OF_WEEK, INDEX_START


Factor_Correcao = {"domingo":1, "segunda":0, "terça":6, "quarta":5, "quinta":4, "sexta":3, "sabado":2}

def get_aula_turno(turno:Turnos):
    return or_(
        between(Aulas.horario_inicio, turno.horario_inicio, turno.horario_fim),
        between(Aulas.horario_fim, turno.horario_inicio, turno.horario_fim)
    )

def get_aula_semana(dia:date):
    wd = dia.weekday()
    wd = (wd+Factor_Correcao[FIRST_DAY_OF_WEEK.lower()])%7
    if INDEX_START == 1:
        wd += 1
    return Aulas_Ativas.id_semana == wd

def get_aula_intervalo(inicio:date, fim:date):
    return or_(
        and_(
            Aulas_Ativas.inicio_ativacao.is_(None),
            Aulas_Ativas.fim_ativacao.is_(None)
        ), and_(
            Aulas_Ativas.inicio_ativacao.is_not(None),
            Aulas_Ativas.fim_ativacao.is_(None),
            Aulas_Ativas.inicio_ativacao <= fim
        ), and_(
            Aulas_Ativas.inicio_ativacao.is_(None),
            Aulas_Ativas.fim_ativacao.is_not(None),
            Aulas_Ativas.fim_ativacao >= inicio
        ), and_(
            Aulas_Ativas.inicio_ativacao.is_not(None),
            Aulas_Ativas.fim_ativacao.is_not(None),
            Aulas_Ativas.inicio_ativacao <= fim,
            Aulas_Ativas.fim_ativacao >= inicio
        )
    )
    
def sort_periodos(descending=False):
    null_case = case(
        (Aulas_Ativas.inicio_ativacao.is_(None), 0),
        else_=1
    )
    order = [
        Aulas_Ativas.tipo_aula,
        Aulas_Ativas.id_semana,
        Aulas_Ativas.id_aula
    ]
    if descending:
        order.append(desc(null_case))
        order.append(Aulas_Ativas.inicio_ativacao.desc())
    else:
        order.append(null_case)
        order.append(Aulas_Ativas.inicio_ativacao)
    return order

def filtro_tipo_responsavel(
    model: Type[ReservaBase],
    tipo: int
) -> ColumnElement[bool]:

    match tipo:
        case 0:
            return model.id_responsavel.isnot(None) & model.id_responsavel_especial.is_(None)
        case 1:
            return model.id_responsavel.is_(None) & model.id_responsavel_especial.isnot(None)
        case 2:
            return model.id_responsavel.isnot(None) & model.id_responsavel_especial.isnot(None)
        case 3:
            return model.id_responsavel.is_(None) & model.id_responsavel_especial.is_(None)
        case _:
            raise ValueError("tipo_responsavel inválido")