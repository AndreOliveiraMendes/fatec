from flask import abort, current_app, session
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.dao.internal.general import get_unique_or_500, handle_db_error
from app.dao.internal.usuarios import get_user
from app.enums import TipoMovimentacaoEnum
from app.extensions import db
from app.models.controle import EquipamentoDisponibilidade
from app.models.equipamentos import Equipamentos
from app.models.historicos import MovimentacaoEquipamento

TIPOS_MOVIMENTACAO = {"ajuste", "reposicao", "manutencao"}

def check_equipamento(id):
    equipamento = db.session.get(Equipamentos, id)
    return equipamento is not None

def ajuste_quantidade(id, quantidade, reservado, dia, observacao):
    userid = int(session.get('userid'))
    user = get_user(userid)
    try: 
        quantidade_equipamento = get_unique_or_500(
            EquipamentoDisponibilidade,
            EquipamentoDisponibilidade.id_equipamento == id,
            EquipamentoDisponibilidade.data == dia            
        )

        if not quantidade_equipamento:
            quantidade_equipamento = EquipamentoDisponibilidade(
                id_equipamento = id,
                data = dia,
                quantidade_total = quantidade
            )
        else:
            quantidade_equipamento.quantidade_total = quantidade

        if quantidade_equipamento.quantidade_total < reservado:
            raise ValueError("Quantidade total inferior a reservada")

        movimentacao_equipamento = MovimentacaoEquipamento(
            id_funcionario = userid,
            id_equipamento = id,
            quantidade = quantidade,
            tipo = TipoMovimentacaoEnum.AJUSTE,
            observacao = observacao
        )

        db.session.add(quantidade_equipamento)
        db.session.add(movimentacao_equipamento)
        db.session.flush()

        nome = getattr(getattr(user, "pessoa", None), "nome_pessoa", "Usuário desconhecido")

        current_app.logger.info(
            "Usuário '%s' ajustou o estoque para %s unidades o equipamento %s",
            nome,
            quantidade_equipamento.quantidade_total,
            quantidade_equipamento.equipamento.nome_equipamento
        )
   
        db.session.commit()
    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao ajustar o estoque", False)
        return 400, "Erro ao ajustar o estoque"
    except ValueError as e:
        handle_db_error(e, "Erro ao ajustar o estoque", False)
        return 400, "Erro ao ajustar o estoque"
    return 0, ""

def reposicao_estoque(id, quantidade, reservado, dia, observacao):
    pass