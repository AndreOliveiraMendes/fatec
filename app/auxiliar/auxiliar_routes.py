import enum
from datetime import date, datetime, timedelta
from typing import (Any, Callable, Literal, MutableMapping, Optional, Type,
                    TypeVar)

from flask import abort, redirect, session, url_for
from flask.typing import ResponseReturnValue
from sqlalchemy import and_, select
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.elements import ColumnElement

from app.auxiliar.constant import PERM_ADMIN
from app.models import (Base, Historicos, Locais, OrigemEnum, Pessoas,
                        ReservaBase, Reservas_Fixas, Reservas_Temporarias,
                        Usuarios, Usuarios_Especiais, db)
from config.general import AFTER_ACTION, LOCAL_TIMEZONE

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

T = TypeVar("T", bound=Base)
V = TypeVar("V")

def none_if_empty(value:Any, cast_type: Callable[[Any], V] = str) -> Optional[V]:
    if value is None:
        return None
    # Se for string, verifica se está vazia ou só com espaços
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        return cast_type(value)
    except (ValueError, TypeError):
        return None

def parse_time_string(value, format = None):
    if not value:
        return None
    try:
        if format:
            return datetime.strptime(value, format).time()
        else:
            return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None
    

def parse_date_string(value, format = None):
    if not value:
        return None
    try:
        if format:
            return datetime.strptime(value, format).date()
        else:
            return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

def parse_datetime_string(value, format = None):
    if not value:
        return None
    try:
        if format:
            return datetime.strptime(value, format)
        else:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None

def get_query_params(request):
    return {key: value for key, value in request.form.items() if key not in IGNORED_FORM_FIELDS}

def get_user_info(userid):
    if not userid:
        return None
    user = db.session.get(Usuarios, userid)
    if user:
        return user
    else:
        session.pop('userid')

def formatar_valor(valor):
    if isinstance(valor, enum.Enum):
        return valor.value
    return valor

def dict_format(dictionary):
    campos = []
    for key in sorted(dictionary.keys()):
        value = dictionary[key]
        campos.append(f"{key}: {value}")
    return "; ".join(campos)

def registrar_log_generico_sistema(acao:Literal['Login'], objeto, antes=None, observacao=None, skip_unchanged=False):
    nome_tabela = getattr(objeto, "__tablename__", objeto.__class__.__name__)
    insp = inspect(objeto)

    # Tenta pegar a primary key dinamicamente
    chaves_primarias = [key.name for key in insp.mapper.primary_key]
    dados_chave = {chave: getattr(objeto, chave) for chave in chaves_primarias}

    campos = []
    for col in objeto.__table__.columns:
        nome = col.name
        valor_novo = getattr(objeto, nome, None)
        valor_novo_fmt = formatar_valor(valor_novo)

        if antes:
            valor_antigo = getattr(antes, nome, None)
            valor_antigo_fmt = formatar_valor(valor_antigo)

            if valor_antigo_fmt != valor_novo_fmt:
                campos.append(f"{nome}: {valor_antigo_fmt} → {valor_novo_fmt}")
        else:
            campos.append(f"{nome}: {valor_novo_fmt}")

    # Evita log vazio (nenhuma mudança real)
    if not campos:
        if skip_unchanged:
            return
        campos.append("nenhuma alteração detectada")

    historico = Historicos(
        id_usuario = None,
        tabela = nome_tabela,
        categoria = acao,
        data_hora = datetime.now(LOCAL_TIMEZONE),
        message = "; ".join(campos),
        chave_primaria = dict_format(dados_chave),
        origem = OrigemEnum('Sistema'),
        observacao = observacao
    )
    db.session.add(historico)

def registrar_log_generico_usuario(userid, acao:Literal['Inserção', 'Edição', 'Exclusão', 'Quick-Setup'], objeto, antes=None, observacao=None, skip_unchanged=False):
    nome_tabela = getattr(objeto, "__tablename__", objeto.__class__.__name__)
    insp = inspect(objeto)

    # Tenta pegar a primary key dinamicamente
    chaves_primarias = [key.name for key in insp.mapper.primary_key]
    dados_chave = {chave: getattr(objeto, chave) for chave in chaves_primarias}

    campos = []
    for col in objeto.__table__.columns:
        nome = col.name
        valor_novo = getattr(objeto, nome, None)
        valor_novo_fmt = formatar_valor(valor_novo)

        if antes:
            valor_antigo = getattr(antes, nome, None)
            valor_antigo_fmt = formatar_valor(valor_antigo)

            if valor_antigo_fmt != valor_novo_fmt:
                campos.append(f"{nome}: {valor_antigo_fmt} → {valor_novo_fmt}")
        else:
            campos.append(f"{nome}: {valor_novo_fmt}")

    # Evita log vazio (nenhuma mudança real)
    if not campos:
        if skip_unchanged:
            return
        campos.append("nenhuma alteração detectada")

    historico = Historicos(
        id_usuario = userid,
        tabela = nome_tabela,
        categoria = acao,
        data_hora = datetime.now(LOCAL_TIMEZONE),
        message = "; ".join(campos),
        chave_primaria = dict_format(dados_chave),
        origem = OrigemEnum('Usuario'),
        observacao = observacao
    )
    db.session.add(historico)

def disable_action(extras, disable):
    extras["disable"] = disable
    for action in disable:
        if action in ['editar', 'excluir']:
            extras[f"disable_{action}"] = True

def include_action(extras, include):
    add = [a['value'] for a in include]
    extras["include"] = include
    extras["add"] = add

def get_session_or_request(request, session, key, default = None):
    return session.pop(key, request.form.get(key, default))

def register_return(url:str, acao:str, extras:Optional[MutableMapping[str, Any]] = None, bloco:int = 0, **args: Any) -> tuple[ResponseReturnValue | None, int | None]:
    if AFTER_ACTION == 'noredirect':
        ret_bloco = bloco
        if extras is not None:
            for k, v in args.items():
                extras[k] = v
        return None, ret_bloco
    elif AFTER_ACTION in ['redirectabertura', 'redirectback']:
        if AFTER_ACTION == 'redirectback':
            session['acao'] = acao
        return redirect(url_for(url)), None
    else:
        raise ValueError(f"Configuração AFTER_ACTION inválida: {AFTER_ACTION}")

def time_range(start:date, end:date, step:int = 1):
    day = start
    while start <= day <= end:
        yield day
        day += timedelta(step)

def get_responsavel_reserva(reserva:Reservas_Fixas|Reservas_Temporarias):
    title = ""
    if reserva.tipo_responsavel == 0 or reserva.tipo_responsavel == 2:
        responsavel = db.get_or_404(Pessoas, reserva.id_responsavel)
        if responsavel.alias:
            title += responsavel.alias
        else:
            title += responsavel.nome_pessoa
    if reserva.tipo_responsavel== 1 or reserva.tipo_responsavel == 2:
        responsavel = db.get_or_404(Usuarios_Especiais, reserva.id_responsavel_especial)
        if reserva.tipo_responsavel == 1:
            title += responsavel.nome_usuario_especial
        else:
            title += f" ({responsavel.nome_usuario_especial})"
    return title

def get_unique_or_500(model: Type[T], *args, **kwargs):
    try:
        return db.session.execute(
            select(model).where(*args, **kwargs)
        ).scalar_one_or_none()
    except MultipleResultsFound:
        abort(500, description=f"Erro ao consultar {model.__name__}.")

def check_local(local:Locais, perm):
    if perm&PERM_ADMIN > 0:
        return
    if local.disponibilidade.value == 'Indisponivel':
        abort(403, description="Local indisponível para reservas.")

def builder_helper_fixa(id_semestre:int, id_lab: int|None=None):
    """Monta helper de reservas fixas indexado por (local, aula)."""
    conditions = [Reservas_Fixas.id_reserva_semestre == id_semestre]
    if id_lab is not None:
        conditions.append(Reservas_Fixas.id_reserva_local == id_lab)
    sel_reservas = select(Reservas_Fixas).where(*conditions)
    reservas = db.session.execute(sel_reservas).scalars().all()
    helper = {}
    for r in reservas:
        title = get_responsavel_reserva(r)
        helper[(r.id_reserva_local, r.id_reserva_aula)] = {"title": title, "id":r.id_reserva_fixa}
    return helper

def builder_helper_temporaria(inicio, fim, id_lab: int|None=None):
    conditions = [
        and_(
            Reservas_Temporarias.inicio_reserva <= fim,
            Reservas_Temporarias.fim_reserva >= inicio
        )
    ]
    if id_lab is not None:
        conditions.append(Reservas_Temporarias.id_reserva_local == id_lab)
    sel_reservas = select(Reservas_Temporarias).where(*conditions)
    reservas = db.session.execute(sel_reservas).scalars().all()
    helper = {}
    for r in reservas:
        title = get_responsavel_reserva(r)
        days = [day.strftime('%Y-%m-%d') for day in time_range(r.inicio_reserva, r.fim_reserva, 7)]
        for day in days:
            helper[(r.id_reserva_local, r.id_reserva_aula, day)] = title
    return helper

def filtro_tipo_responsavel(
    model: Type[ReservaBase],
    tipo: int
) -> ColumnElement[bool]:
    match tipo:
        case 0:
            return (
                model.id_responsavel.isnot(None)
                & model.id_responsavel_especial.is_(None)
            )
        case 1:
            return (
                model.id_responsavel.is_(None)
                & model.id_responsavel_especial.isnot(None)
            )
        case 2:
            return (
                model.id_responsavel.isnot(None)
                & model.id_responsavel_especial.isnot(None)
            )
        case 3:
            return (
                model.id_responsavel.is_(None)
                & model.id_responsavel_especial.is_(None)
            )
        case _:
            raise ValueError("tipo_responsavel inválido")