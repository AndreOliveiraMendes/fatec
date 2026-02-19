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

# =========================================================
# CONSTANTES / TYPES
# =========================================================
IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

T = TypeVar("T", bound=Base)
V = TypeVar("V")


# =========================================================
# PARSERS / CAST HELPERS
# =========================================================
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

def _parse_generic(value, format, extractor=None):
    if not value:
        return None
    try:
        dt = datetime.strptime(value, format)
        return extractor(dt) if extractor else dt
    except ValueError:
        return None

def parse_time_string(value, format=None):
    return _parse_generic(
        value,
        format or "%H:%M",
        extractor=lambda dt: dt.time()
    )

def parse_date_string(value, format=None):
    return _parse_generic(
        value,
        format or "%Y-%m-%d",
        extractor=lambda dt: dt.date()
    )

def parse_datetime_string(value, format=None):
    return _parse_generic(
        value,
        format or "%Y-%m-%dT%H:%M"
    )

# =========================================================
# REQUEST / SESSION HELPERS
# =========================================================
def get_query_params(request):
    return {
        key: value
        for key, value in request.form.items()
        if key not in IGNORED_FORM_FIELDS
    }


def get_session_or_request(request, session, key, default=None):
    return session.pop(key, request.form.get(key, default))


def get_user(userid):
    if not userid:
        return None

    user = db.session.get(Usuarios, userid)
    if user:
        return user

    current_app.logger.error(f"Usuário com ID {userid} não encontrado.")
    session.pop('userid')


# =========================================================
# FORMATADORES
# =========================================================
def formatar_valor(valor):
    if isinstance(valor, enum.Enum):
        return valor.value
    return valor


def dict_format(dictionary):
    campos = []
    for key in sorted(dictionary.keys()):
        campos.append(f"{key}: {dictionary[key]}")
    return "; ".join(campos)


# =========================================================
# LOGGING
# =========================================================
def _registrar_log_generico(
    *,
    usuario_id,
    origem,
    acao,
    objeto,
    antes=None,
    observacao=None,
    skip_unchanged=False
):
    nome_tabela = getattr(objeto, "__tablename__", objeto.__class__.__name__)
    insp = inspect(objeto)

    chaves_primarias = [key.name for key in insp.mapper.primary_key]
    dados_chave = {chave: getattr(objeto, chave) for chave in chaves_primarias}

    campos = []
    for col in objeto.__table__.columns:
        nome = col.name
        valor_novo_fmt = formatar_valor(getattr(objeto, nome, None))

        if antes:
            valor_antigo_fmt = formatar_valor(getattr(antes, nome, None))
            if valor_antigo_fmt != valor_novo_fmt:
                campos.append(f"{nome}: {valor_antigo_fmt} → {valor_novo_fmt}")
        else:
            campos.append(f"{nome}: {valor_novo_fmt}")

    if not campos:
        if skip_unchanged:
            return
        campos.append("nenhuma alteração detectada")

    db.session.add(Historicos(
        id_usuario=usuario_id,
        tabela=nome_tabela,
        categoria=acao,
        data_hora=datetime.now(LOCAL_TIMEZONE),
        message="; ".join(campos),
        chave_primaria=dict_format(dados_chave),
        origem=OrigemEnum(origem),
        observacao=observacao
    ))


def registrar_log_generico_sistema(
    acao: Literal['Login'],
    objeto,
    antes=None,
    observacao=None,
    skip_unchanged=False
):
    _registrar_log_generico(
        usuario_id=None,
        origem="Sistema",
        acao=acao,
        objeto=objeto,
        antes=antes,
        observacao=observacao,
        skip_unchanged=skip_unchanged
    )


def registrar_log_generico_usuario(
    userid,
    acao: Literal['Inserção', 'Edição', 'Exclusão', 'Quick-Setup'],
    objeto,
    antes=None,
    observacao=None,
    skip_unchanged=False
):
    _registrar_log_generico(
        usuario_id=userid,
        origem="Usuario",
        acao=acao,
        objeto=objeto,
        antes=antes,
        observacao=observacao,
        skip_unchanged=skip_unchanged
    )

# =========================================================
# ACTION HELPERS
# =========================================================
def disable_action(extras, disable):
    extras["disable"] = disable
    for action in disable:
        if action in ['editar', 'excluir']:
            extras[f"disable_{action}"] = True


def include_action(extras, include):
    add = [a['value'] for a in include]
    extras["include"] = include
    extras["add"] = add


def register_return(
    url: str,
    acao: str,
    extras: Optional[MutableMapping[str, Any]] = None,
    bloco: int = 0,
    **args: Any
) -> tuple[ResponseReturnValue | None, int | None]:

    if AFTER_ACTION == 'noredirect':
        if extras is not None:
            extras.update(args)
        return None, bloco

    if AFTER_ACTION in ['redirectabertura', 'redirectback']:
        if AFTER_ACTION == 'redirectback':
            session['acao'] = acao
        return redirect(url_for(url)), None

    raise ValueError(f"Configuração AFTER_ACTION inválida: {AFTER_ACTION}")


# =========================================================
# UTILS GERAIS
# =========================================================
def time_range(start: date, end: date, step: int = 1):
    day = start
    while start <= day <= end:
        yield day
        day += timedelta(step)


def get_unique_or_500(model: Type[T], *args, **kwargs):
    try:
        return db.session.execute(
            select(model).where(*args, **kwargs)
        ).scalar_one_or_none()
    except MultipleResultsFound:
        abort(500, description=f"Erro ao consultar {model.__name__}.")


def check_local(local: Locais, perm):
    if perm & PERM_ADMIN > 0:
        return
    if local.disponibilidade.value == 'Indisponivel':
        abort(403, description="Local indisponível para reservas.")


# =========================================================
# RESERVA HELPERS
# =========================================================
def get_responsavel_reserva(reserva: Reservas_Fixas | Reservas_Temporarias):
    title = ""

    if reserva.tipo_responsavel in (0, 2):
        responsavel = db.get_or_404(Pessoas, reserva.id_responsavel)
        title += responsavel.alias or responsavel.nome_pessoa

    if reserva.tipo_responsavel in (1, 2):
        responsavel = db.get_or_404(Usuarios_Especiais, reserva.id_responsavel_especial)
        title += (
            responsavel.nome_usuario_especial
            if reserva.tipo_responsavel == 1
            else f" ({responsavel.nome_usuario_especial})"
        )

    return title


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


# =========================================================
# BUILDERS DE TABELA
# =========================================================
def builder_helper_fixa(extras, info):
    aulas = set()
    semanas = set()
    row = {}

    for aula_ativa, aula, semana in info:
        aulas.add(aula)
        semanas.add(semana)
        row[(aula.id_aula, semana.id_semana)] = aula_ativa.id_aula_ativa

    extras['head'] = sorted(semanas, key=lambda s: s.id_semana)
    extras['first_col'] = sorted(aulas, key=lambda a: a.horario_inicio)
    extras['row'] = row


def builder_helper_temporaria(extras, aulas):
    table_aulas = []
    table_dias = []

    for info in aulas:
        par = (info.horario_inicio, info.horario_fim)
        if par not in table_aulas:
            table_aulas.append(par)

    table_aulas.sort(key=lambda e: e[0])
    size = len(table_aulas)

    for info in aulas:
        dia = info.dia_consulta
        semana = info.nome_semana

        for i, v in enumerate(table_dias):
            if v['dia'] == dia:
                index_dia = i
                break
        else:
            table_dias.append({'dia': dia, 'semana': semana, 'infos': [None]*size})
            index_dia = len(table_dias) - 1

        for i, v in enumerate(table_aulas):
            if info.horario_inicio == v[0] and info.horario_fim == v[1]:
                table_dias[index_dia]['infos'][i] = info
                break

    extras['head'] = table_aulas
    extras['dias'] = table_dias


# =========================================================
# PERMISSÕES / CHECKS
# =========================================================
def check_ownership_or_admin(reserva: Reservas_Fixas | Reservas_Temporarias):
    userid = session.get('userid')
    user = db.get_or_404(Usuarios, userid)
    perm = db.session.get(Permissoes, userid)

    if reserva.id_responsavel != user.pessoa.id_pessoa and (
        not perm or perm.permissao & PERM_ADMIN == 0
    ):
        abort(403, description="Acesso negado à reserva de outro usuário.")


def check_periodo_fixa(reserva: Reservas_Fixas):
    userid = session.get('userid')
    perm = db.session.get(Permissoes, userid)

    if perm and perm.permissao & PERM_ADMIN:
        return True

    hoje = date.today()
    return reserva.semestre.data_inicio_reserva <= hoje <= reserva.semestre.data_fim_reserva


# =========================================================
# INFO JSON RESERVAS
# =========================================================
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