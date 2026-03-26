from flask import abort, current_app, session
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.dao.internal.general import get_unique_or_500, handle_db_error
from app.dao.internal.usuarios import get_user
from app.enums import TipoMovimentacaoEnum
from app.extensions import db
from app.models.controle import EquipamentoDisponibilidade
from app.models.historicos import MovimentacaoEquipamento


def ajuste_quantidade(id, quantidade, dia, observacao):
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
        handle_db_error(e, "Erro ao ajustar o estoque")
        return 400, "Erro ao ajustar o estoque"
    return 0, ""