import enum
from datetime import date, datetime, time
from typing import Any, Callable, Optional, Type, TypeVar, overload

from sqlalchemy import ColumnElement, and_, between, case, desc, or_

from app.model.aulas import Aulas, Aulas_Ativas, Turnos
from app.model.reservas.reservas_laboratorios import ReservaBase, Reservas_Fixas, Reservas_Temporarias
from config.general import FIRST_DAY_OF_WEEK, INDEX_START

V = TypeVar("V")
S = TypeVar("S")

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

def check_first(reserva_fixa:Reservas_Fixas, reserva_temporaria:Reservas_Temporarias):
    if reserva_fixa.id_reserva_local < reserva_temporaria.id_reserva_local:
        return 0
    elif reserva_fixa.id_reserva_local > reserva_temporaria.id_reserva_local:
        return 1
    else:
        if reserva_fixa.aula_ativa.aula.horario_inicio < reserva_temporaria.aula_ativa.aula.horario_inicio:
            return 0
        elif reserva_fixa.aula_ativa.aula.horario_inicio > reserva_temporaria.aula_ativa.aula.horario_inicio:
            return 1
        else:
            return 2
        
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

def formatar_valor(valor):
    if isinstance(valor, enum.Enum):
        return valor.value
    return valor

def dict_format(dictionary):
    campos = []
    for key in sorted(dictionary.keys()):
        campos.append(f"{key}: {dictionary[key]}")
    return "; ".join(campos)

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

def none_if_empty(value: Any, cast_type: Callable[[Any], V] = str) -> Optional[V]:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    try:
        return cast_type(value)
    except (ValueError, TypeError):
        return None
    
@overload
def _parse_generic(
    value: str | None,
    format: str,
    extractor: Callable[[datetime], S]
) -> S | None: ...
@overload
def _parse_generic(
    value: str | None,
    format: str,
    extractor: None = None
) -> datetime | None: ...

def _parse_generic(
    value: str | None,
    format: str,
    extractor: Callable[[datetime], S] | None = None
) -> Optional[S | datetime]:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, format)
        return extractor(dt) if extractor else dt
    except ValueError:
        return None

def parse_time_string(value: str | None, format: str | None = None) -> Optional[time]:
    return _parse_generic(
        value,
        format or "%H:%M",
        extractor=lambda dt: dt.time()
    )


def parse_date_string(value: str | None, format: str | None = None) -> Optional[date]:
    return _parse_generic(
        value,
        format or "%Y-%m-%d",
        extractor=lambda dt: dt.date()
    )


def parse_datetime_string(value: str | None, format: str | None = None) -> Optional[datetime]:
    return _parse_generic(
        value,
        format or "%Y-%m-%dT%H:%M"
    )