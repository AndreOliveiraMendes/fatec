from app.models.controle import Exibicao_Reservas
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)


def resolver_reserva(temp:Reservas_Temporarias|None, fixa:Reservas_Fixas|None, exibicao:Exibicao_Reservas|None):
    choose = temp or fixa

    tipo = (
        "temporaria" if temp
        else "fixa" if fixa
        else "neither"
    )

    if exibicao:
        if exibicao.tipo_reserva.value == "fixa":
            choose = fixa
            tipo = "fixa"
        elif exibicao.tipo_reserva.value == "temporaria":
            choose = temp
            tipo = "temporaria"

        tipo = {
            "fixa": "fixa",
            "temporaria": "temporaria"
        }.get(
            exibicao.tipo_reserva.value,
            tipo
        )

    return choose, tipo