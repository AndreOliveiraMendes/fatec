import enum
from flask import request
from datetime import datetime
from app.models import db, Usuarios, Pessoas, Permissoes, Historicos
from sqlalchemy.inspection import inspect

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

def none_if_empty(value, cast_type=str):
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

def parse_time_string(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None

def get_query_params(request):
    return {key: value for key, value in request.form.items() if key not in IGNORED_FORM_FIELDS}

def get_user_info(userid):
    username, perm = None, 0
    if not userid:
        return username, perm
    user = Usuarios.query.get(userid)
    if user:
        pessoa = Pessoas.query.get(user.id_pessoa)
        username = pessoa.nome_pessoa
        permissao = Permissoes.query.get(userid)
        if permissao:
            perm = permissao.permissao
    return username, perm

def formatar_valor(valor):
    if isinstance(valor, enum.Enum):
        return valor.value
    return valor

def dict_format(dictionary):
    campos = []
    for key, value in dictionary.items():
        campos.append(f"{key}: {value}")
    return "; ".join(campos)

def registrar_log_generico(userid, acao, objeto, antes=None, observacao=None, skip_unchanged=False):
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

            if valor_antigo != valor_novo:
                campos.append(f"{nome}: {valor_antigo_fmt} → {valor_novo_fmt}")
        else:
            campos.append(f"{nome}: {valor_novo_fmt}")

    # Evita log vazio (nenhuma mudança real)
    if not campos:
        if skip_unchanged:
            return
        campos.append("nenhuma alteração detectada")

    user = Usuarios.query.get(userid);

    historico = Historicos(
        id_usuario = userid,
        id_pessoa = user.id_pessoa,
        tabela = nome_tabela,
        categoria = acao,
        data_hora = datetime.now(),
        message = "; ".join(campos),
        chave_primaria = dict_format(dados_chave),
        observacao = observacao
    )
    db.session.add(historico)

def disable_action(extras, disable):
    extras["disable"] = disable
    for action in disable:
        if action in ['editar', 'excluir']:
            extras[f"disable_{action}"] = True