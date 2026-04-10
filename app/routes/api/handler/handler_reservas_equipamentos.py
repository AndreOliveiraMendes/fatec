from datetime import datetime

from flask import current_app, session, url_for
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS, Permission
from app.dao.internal.general import handle_db_error
from app.dao.internal.usuarios import get_user
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
            "id_reserva": reserva.id_reserva,
            "nome": eq['nome_equipamento'],
            "quantidade": qtd,
            "devolvido": devolvido,
            "estado_item": status,
            "url_atualizar": url_for('api_reservas_equipamentos.registrar_devolucao_equipamento', id_reserva=reserva.id_reserva, id_equipamento=eq['id_equipamento'])
        })

    return res

def check_cancelamento_permissao(reserva: Reservas_Equipamentos):
    userid = session.get('userid')
    if not userid:
        return False
    
    user = get_user(userid)
    if not user:
        return False
    
    if user.perm.has(Permission.ADMIN):
        return True
    
    return reserva.id_responsavel == userid

def cancelar_reserva_equipamento_handler(reserva: Reservas_Equipamentos, motivo: str):
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
        userid = session.get('userid')

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

    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao cancelar reserva de equipamento", show_flash_message=False)
        return 500, 'Erro interno ao cancelar reserva de equipamento'

    except (ValueError, TypeError) as e:
        handle_db_error(e, "Erro ao cancelar reserva de equipamento", show_flash_message=False)
        return 400, 'ID de usuário inválido'
    
def aprovar_reserva_equipamento_handler(reserva: Reservas_Equipamentos):
    if reserva.estado != StatusReservaEquipamentoEnum.PENDENTE:
        current_app.logger.warning(
            f"Tentativa de aprovar reserva não pendente | reserva_id={reserva.id_reserva} estado_atual={reserva.estado}"
        )
        return 400, 'Apenas reservas pendentes podem ser aprovadas'
    
    try:
        userid = session.get('userid')

        reserva.estado = StatusReservaEquipamentoEnum.ATIVA

        db.session.add(reserva)
        db.session.commit()

        current_app.logger.info(
            f"Reserva aprovada | reserva_id={reserva.id_reserva} "
            f"usuario_id={userid}"
        )

        return 200, 'ok'
    
    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao aprovar reserva de equipamento", show_flash_message=False)
        return 500, 'Erro interno ao aprovar reserva de equipamento'

def get_item_reserva(id_reserva, id_equipamento):
    sel_item = (
        select(Reserva_Equipamento_Item)
        .where(
            Reserva_Equipamento_Item.id_reserva == id_reserva,
            Reserva_Equipamento_Item.id_equipamento == id_equipamento
        )
    )

    return db.session.execute(sel_item).scalar_one_or_none()

def registrar_devolucao_equipamento_handler(item: Reserva_Equipamento_Item, qtd_devolvida: int):
    try:
        item.devolvido = qtd_devolvida
        db.session.add(item)
        db.session.commit()

        current_app.logger.info(
            f"Devolução registrada | reserva_id={item.id_reserva} "
            f"equipamento_id={item.id_equipamento} quantidade_devolvida={qtd_devolvida}"
        )

        return 200, 'ok'

    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao registrar devolução de equipamento", show_flash_message=False)
        return 500, 'Erro interno ao registrar devolução de equipamento'
    
def finalizar_reserva_se_concluida(reserva: Reservas_Equipamentos):
    if not all(item.devolvido == item.quantidade for item in reserva.itens):
        return 200, 'ok'

    try:
        reserva.estado = StatusReservaEquipamentoEnum.CONCLUIDA
        db.session.commit()

        current_app.logger.info(
            f"Reserva concluída automaticamente | reserva_id={reserva.id_reserva}"
        )

        return 200, 'ok'

    except DB_ERRORS as e:
        handle_db_error(e, "Erro ao finalizar reserva de equipamento", show_flash_message=False)
        return 500, 'Erro interno ao finalizar reserva de equipamento'