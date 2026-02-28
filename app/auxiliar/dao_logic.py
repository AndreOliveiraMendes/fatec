from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)


def check_first(reserva_fixa:Reservas_Fixas, reserva_temporaria:Reservas_Temporarias):
    if reserva_fixa.id_reserva_local < reserva_temporaria.id_reserva_local:
        return 0
    elif reserva_fixa.id_reserva_local > reserva_temporaria.id_reserva_local:
        return 1
    else:
        if reserva_fixa.aula_ativa.aula.horario_inicio < reserva_temporaria.aula_ativa.aula.horario_inicio:
            return 0
        elif reserva_fixa.aula_ativa.aula.horario_inicio > reserva_temporaria.aula_ativa.aula.horario_inicio:
            return 1
        else:
            return 2