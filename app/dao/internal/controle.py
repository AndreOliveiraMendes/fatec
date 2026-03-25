from datetime import date

from flask import abort
from sqlalchemy import func, select
from sqlalchemy.exc import MultipleResultsFound

from app.enums import TipoReservaEnum
from app.extensions import db
from app.models.aulas import Aulas_Ativas
from app.models.controle import (EquipamentoDisponibilidade, Exibicao_Reservas,
                                 Situacoes_Das_Reserva)
from app.models.equipamentos import Equipamentos
from app.models.locais import Locais


def get_situacoes_por_dia(aula:Aulas_Ativas, local:Locais, dia:date, tipo_reserva):
    sel_situacoes = select(
        Situacoes_Das_Reserva
    ).where(
        Situacoes_Das_Reserva.id_situacao_aula == aula.id_aula_ativa,
        Situacoes_Das_Reserva.id_situacao_local == local.id_local,
        Situacoes_Das_Reserva.situacao_dia == dia,
        Situacoes_Das_Reserva.tipo_reserva == TipoReservaEnum(tipo_reserva)
    )
    try:
        return db.session.execute(sel_situacoes).scalar_one_or_none()
    except MultipleResultsFound:
        abort(500, description="Erro ao consultar situação da reserva.")

def get_exibicao_por_dia(aula:Aulas_Ativas, local:Locais, dia:date):
    sel_exibicao = select(
        Exibicao_Reservas
    ).where(
        Exibicao_Reservas.id_exibicao_aula == aula.id_aula_ativa,
        Exibicao_Reservas.id_exibicao_local == local.id_local,
        Exibicao_Reservas.exibicao_dia == dia
    )
    try:
        return db.session.execute(sel_exibicao).scalar_one_or_none()
    except MultipleResultsFound:
        abort(500, description="Erro ao consultar exibição da reserva.")

def get_situacoes():
    sel_situacoes_das_reservas = select(Situacoes_Das_Reserva)
    return db.session.execute(sel_situacoes_das_reservas).scalars().all()

def get_exibicoes():
    sel_exibicoes_das_reservas = select(Exibicao_Reservas)
    return db.session.execute(sel_exibicoes_das_reservas).scalars().all()

def get_equipamento_disponibilidades():
    sel_disponibilidades = select(EquipamentoDisponibilidade)
    return db.session.execute(sel_disponibilidades).scalars().all()

from sqlalchemy import select, func

def get_equipamento_disponibilidade_dia(dia, id_equipamento=None):
    subq = (
        select(EquipamentoDisponibilidade.quantidade_total)
        .where(
            EquipamentoDisponibilidade.id_equipamento == Equipamentos.id_equipamento,
            EquipamentoDisponibilidade.data <= dia
        )
        .order_by(EquipamentoDisponibilidade.data.desc())
        .limit(1)
        .scalar_subquery()
    )

    stmt = select(
        Equipamentos.id_equipamento,
        func.coalesce(subq, 0).label("quantidade")
    )

    # 🔥 filtro opcional
    if id_equipamento:
        stmt = stmt.where(Equipamentos.id_equipamento == id_equipamento)

    result = db.session.execute(stmt).all()

    # 🔹 se for específico → retorna int
    if id_equipamento is not None:
        return result[0].quantidade if result else 0

    # 🔹 se for geral → retorna dict
    return {row.id_equipamento: row.quantidade for row in result}