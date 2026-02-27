from datetime import datetime
from typing import Literal

from sqlalchemy import inspect

from app.auxiliar.auxiliar_dao import dict_format, formatar_valor
from app.enums import OrigemEnum
from app.extensions import db
from app.model.historicos import Historicos
from config.general import LOCAL_TIMEZONE


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