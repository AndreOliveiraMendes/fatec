from app.auxiliar.dao_logic import check_first
from app.dao.internal.controle import get_exibicao_por_dia


def process_reservas(reservas_fixas, reservas_temporarias, reserva_dia):
    reservas = []
    i, j = 0, 0
    control_1 = len(reservas_fixas) if reservas_fixas else 0
    control_2 = len(reservas_temporarias) if reservas_temporarias else 0
    while i < control_1 or j < control_2:
        reserva = {}
        if i < control_1 and j < control_2:
            rf = reservas_fixas[i]
            rt = reservas_temporarias[j]
            who = check_first(rf, rt)
            if who == 0:
                reserva['horario'] = rf.aula_ativa
                reserva['local'] = rf.local
                reserva['fixa'] = rf
                reserva['temporaria'] = None
                i += 1
            elif who == 1:
                reserva['horario'] = rt.aula_ativa
                reserva['local'] = rt.local
                reserva['fixa'] = None
                reserva['temporaria'] = rt
                j += 1
            else:
                reserva['horario'] = rf.aula_ativa
                reserva['local'] = rf.local
                reserva['fixa'] = rf
                reserva['temporaria'] = rt
                i += 1
                j += 1
        elif i < control_1:
            rf = reservas_fixas[i]
            reserva['horario'] = rf.aula_ativa
            reserva['local'] = rf.local
            reserva['fixa'] = rf
            reserva['temporaria'] = None
            i += 1
        else:
            rt = reservas_temporarias[j]
            reserva['horario'] = rt.aula_ativa
            reserva['local'] = rt.local
            reserva['fixa'] = None
            reserva['temporaria'] = rt
            j += 1
        reserva['exibicao'] = get_exibicao_por_dia(reserva['horario'], reserva['local'], reserva_dia)
        reservas.append(reserva)
    return reservas