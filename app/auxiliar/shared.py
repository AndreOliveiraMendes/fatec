from datetime import datetime

from sqlalchemy import between

from app.dao.internal.general import get_unique_or_500
from app.models.aulas import Semestres
from app.models.controle import Exibicao_Reservas
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)
from app.routes_helper.ui import montar_partes_reserva


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

def get_reserva(lab, aula, dia, mostrar_icone=False, tela_televisor=False, tela=None):
    fixa, temp, choose = None, None, None
    semestre = get_unique_or_500(
        Semestres,
        between(dia, Semestres.data_inicio, Semestres.data_fim)
    )
    if semestre:
        fixa = get_unique_or_500(
            Reservas_Fixas,
            Reservas_Fixas.id_reserva_local == lab,
            Reservas_Fixas.id_reserva_aula == aula,
            Reservas_Fixas.id_reserva_semestre == semestre.id_semestre
        )
    if isinstance(dia, datetime):
        dia = dia.date()
    temp = get_unique_or_500(
        Reservas_Temporarias,
        Reservas_Temporarias.id_reserva_local == lab,
        Reservas_Temporarias.id_reserva_aula == aula,
        between(dia, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva)
    )
    
    exibicao = get_unique_or_500(
        Exibicao_Reservas,
        Exibicao_Reservas.id_exibicao_local == lab,
        Exibicao_Reservas.id_exibicao_aula == aula,
        Exibicao_Reservas.exibicao_dia == dia
    )

    choose, _ = resolver_reserva(temp, fixa, exibicao)

    partes = montar_partes_reserva(
        choose,
        mostrar_icone=mostrar_icone,
        lab=lab,
        aula=aula,
        dia=dia,
        tela_televisor=tela_televisor,
        tela=tela
    )
    
    return partes