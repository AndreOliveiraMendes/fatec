import enum
from datetime import date, datetime, timedelta
from typing import (Any, Callable, Literal, MutableMapping, Optional, Type,
                    TypeVar)

from flask import abort, current_app, redirect, session, url_for
from flask.typing import ResponseReturnValue
from sqlalchemy import and_, select
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.inspection import inspect
from sqlalchemy.sql.elements import ColumnElement

from app.auxiliar.constant import PERM_ADMIN
from app.models import (Base, Historicos, Locais, OrigemEnum, Permissoes,
                        Pessoas, ReservaBase, Reservas_Fixas,
                        Reservas_Temporarias, Usuarios, Usuarios_Especiais, db)
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
        current_app.logger.error(f"Usuário com ID {userid} não encontrado.")
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

def builder_helper_fixa(extras, info):
    """Monta helper de reservas fixas para montar a tabela de reservas"""
    aulas = set()
    semanas = set()
    row = {}
    for aula_ativa, aula, semana in info:
        aulas.add(aula)
        semanas.add(semana)
        row[(aula.id_aula, semana.id_semana)] = aula_ativa.id_aula_ativa
    aulas = sorted(aulas, key=lambda a: a.horario_inicio)
    semanas = sorted(semanas, key=lambda s: s.id_semana)
    extras['head'] = semanas
    extras['first_col'] = aulas
    extras['row'] = row
    

def builder_helper_temporaria(extras, aulas):
    table_aulas = []
    table_dias = []
    for info in aulas:
        if not (info.horario_inicio, info.horario_fim) in table_aulas:
            table_aulas.append((info.horario_inicio, info.horario_fim))
    table_aulas.sort(key = lambda e:e[0])
    size = len(table_aulas)
    for info in aulas:
        dia = info.dia_consulta
        semana = info.nome_semana
        hora_inicio = info.horario_inicio
        hora_fim = info.horario_fim
        index_dia, index_aula = None, None;
        for i, v in enumerate(table_dias):
            if v['dia'] == dia:
                index_dia = i
                break
        else:
            table_dias.append({'dia':dia, 'semana':semana, 'infos':[None]*size})
            index_dia = len(table_dias) - 1
        for i, v in enumerate(table_aulas):
            if hora_inicio == v[0] and hora_fim == v[1]:
                index_aula = i
                break
        table_dias[index_dia]['infos'][index_aula] = info
    extras['head'] = table_aulas
    extras['dias'] = table_dias

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
        
# informações das reservas

def check_ownership_or_admin(reserva:Reservas_Fixas|Reservas_Temporarias):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    perm = db.session.get(Permissoes, userid)
    if reserva.id_responsavel != user.pessoa.id_pessoa and (not perm or perm.permissao&PERM_ADMIN == 0):
        abort(403, description="Acesso negado à reserva de outro usuário.")
        
def check_periodo_fixa(reserva:Reservas_Fixas):
    userid = session.get('userid')
    #user = db.get_or_404(Usuarios, userid)
    perm = db.session.get(Permissoes, userid)
    if perm and perm.permissao & PERM_ADMIN:
        return True
    hoje = date.today()
    if reserva.semestre.data_inicio_reserva > hoje or reserva.semestre.data_fim_reserva < hoje:
        return False
    return True

def info_reserva_fixa(id_reserva):
    reserva = db.get_or_404(Reservas_Fixas, id_reserva)
    check_ownership_or_admin(reserva)
    return {
        "local": reserva.local.nome_local,
        "semestre": reserva.semestre.nome_semestre,
        "semana": reserva.aula_ativa.dia_da_semana.nome_semana,
        "horario": f"{reserva.aula_ativa.aula.horario_inicio:%H:%M} às {reserva.aula_ativa.aula.horario_fim:%H:%M}",
        "observacao": reserva.observacoes,
        "finalidadereserva": reserva.finalidade_reserva.value,
        "responsavel": reserva.id_responsavel,
        "responsavel_especial": reserva.id_responsavel_especial,
        "cancel_url": url_for("usuario.cancelar_reserva", tipo_reserva="fixa", id_reserva=id_reserva),
        "editar_url": url_for("usuario.editar_reserva", tipo_reserva="fixa", id_reserva=id_reserva)
    }

def info_reserva_temporaria(id_reserva):
    reserva = db.get_or_404(Reservas_Temporarias, id_reserva)
    check_ownership_or_admin(reserva)
    return {
        "local": reserva.local.nome_local,
        "periodo": f"{reserva.inicio_reserva} - {reserva.fim_reserva}",
        "semana": reserva.aula_ativa.dia_da_semana.nome_semana,
        "horario": f"{reserva.aula_ativa.aula.horario_inicio:%H:%M} às {reserva.aula_ativa.aula.horario_fim:%H:%M}",
        "observacao": reserva.observacoes,
        "finalidadereserva": reserva.finalidade_reserva.value,
        "responsavel": reserva.id_responsavel,
        "responsavel_especial": reserva.id_responsavel_especial,
        "cancel_url": url_for("usuario.cancelar_reserva", tipo_reserva="temporaria", id_reserva=id_reserva),
        "editar_url": url_for("usuario.editar_reserva", tipo_reserva="temporaria", id_reserva=id_reserva)
    }