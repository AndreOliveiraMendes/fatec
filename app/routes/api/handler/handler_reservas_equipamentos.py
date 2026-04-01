from datetime import datetime

from flask import current_app, session
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.dao.internal.general import handle_db_error
from app.enums import StatusReservaEquipamentoEnum
from app.extensions import db
from app.models.equipamentos import Equipamentos
from app.models.reservas.reservas_equipamentos import (
    Reserva_Equipamento_Item, Reservas_Equipamentos)
from config.general import LOCAL_TIMEZONE


def get_items_reserva_equipamento(id_reserva):
    sel = (
        select(
            Reserva_Equipamento_Item.id_equipamento,
            Equipamentos.nome_equipamento,
            Reserva_Equipamento_Item.quantidade,
            Reserva_Equipamento_Item.devolvido
        )
        .join(Reservas_Equipamentos)
        .join(Equipamentos)
        .where(Reservas_Equipamentos.id_reserva == id_reserva)
    )
    return db.session.execute(sel).mappings().all()

def build_detalhes_reserva(reserva: Reservas_Equipamentos):
    res = {
        "id_reserva": reserva.id_reserva,
        "estado_reserva": reserva.estado,
        "data_reserva": reserva.data_reserva.isoformat(),
        "equipamentos": []
    }

    for eq in get_items_reserva_equipamento(reserva.id_reserva):
        qtd = eq['quantidade']
        devolvido = eq['devolvido']

        if devolvido == qtd:
            status = "Devolvido"
        elif devolvido > 0:
            status = "Parcial"
        else:
            status = "Pendente"

        res["equipamentos"].append({
            "id": eq['id_equipamento'],
            "nome": eq['nome_equipamento'],
            "quantidade": qtd,
            "devolvido": devolvido,
            "estado_item": status
        })

    return res

def cancelar_reserva_equipamento_handler(reserva, motivo: str):
    if reserva.estado == StatusReservaEquipamentoEnum.CANCELADA:
        current_app.logger.warning(
            f"Tentativa de cancelar reserva já cancelada | reserva_id={reserva.id_reserva}"
        )
        return 400, 'Reserva já cancelada'

    if reserva.estado == StatusReservaEquipamentoEnum.CONCLUIDA:
        current_app.logger.warning(
            f"Tentativa de cancelar reserva concluída | reserva_id={reserva.id_reserva}"
        )
        return 400, 'Reserva já concluída, não pode ser cancelada'
    
    try:
        userid = int(session.get('userid'))

        reserva.estado = StatusReservaEquipamentoEnum.CANCELADA
        reserva.motivo_cancelamento = motivo
        reserva.cancelado_por_id = userid
        reserva.cancelado_em = datetime.now(tz=LOCAL_TIMEZONE)

        db.session.add(reserva)
        db.session.commit()

        current_app.logger.info(
            f"Reserva cancelada | reserva_id={reserva.id_reserva} "
            f"usuario_id={userid} motivo='{motivo}'"
        )

        return 200, 'ok'

    except DB_ERRORS:
        current_app.logger.exception(
            f"Erro ao cancelar reserva | reserva_id={reserva.id_reserva}"
        )
        return 500, 'Erro interno ao cancelar reserva de equipamento'

    except (ValueError, TypeError):
        current_app.logger.warning(
            f"ID de usuário inválido ao cancelar reserva | reserva_id={reserva.id_reserva}"
        )
        return 400, 'ID de usuário inválido'
    