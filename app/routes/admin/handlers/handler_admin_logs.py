from datetime import datetime

from flask import request

from app.models.historicos import Historicos


def apply_log_filters(stmt):
    tabela = request.args.get("tabela")
    categoria = request.args.get("categoria")
    origem = request.args.get("origem")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")
    chave_primaria = request.args.get("chave_primaria")
    q = request.args.get("q")
    if tabela:
        stmt = stmt.where(Historicos.tabela == tabela)
    if categoria:
        stmt = stmt.where(Historicos.categoria == categoria)
    if chave_primaria:
        stmt = stmt.where(Historicos.chave_primaria.ilike(f"%{chave_primaria}%"))
    if q:
        stmt = stmt.where(Historicos.message.ilike(f"%{q}%"))
    if origem:
        stmt = stmt.where(Historicos.origem == origem)
    if data_inicio:
        stmt = stmt.where(Historicos.data_hora >= datetime.fromisoformat(data_inicio))
    if data_fim:
        stmt = stmt.where(Historicos.data_hora <= datetime.fromisoformat(data_fim))
    return stmt