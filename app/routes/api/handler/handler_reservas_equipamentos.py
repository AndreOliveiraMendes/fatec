from app.extensions import db
from app.models.equipamentos import Equipamentos
from app.models.reservas.reservas_equipamentos import Reserva_Equipamento_Item, Reservas_Equipamentos
from sqlalchemy import select


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
        "reserva_id": reserva.id_reserva,
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