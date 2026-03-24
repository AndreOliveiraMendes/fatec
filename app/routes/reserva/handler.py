from app.auxiliar.shared import get_reserva

def divide(l, q):
    result = []
    qt = len(l)
    start = 0
    extra = qt%q
    merge = extra <= qt
    qtq = qt//q
    for g in range(qtq):
        end = start + q + (1 if merge and g < extra else 0)
        end = min(end, qt)
        result.append(l[start:end])
        start += end - start
    else:
        if start < qt:
            result.append(l[start:])
    return result

def merge_aulas(modo, aulas, lab, dia):
    if modo == 'multiplo':
        horarios = []
        for aula in aulas:
            if horarios:
                horario = horarios[-1]
                print(horario[-1][0].id_aula_ativa, aula[0].id_aula_ativa)
            else:
                horarios.append([aula])
    return aulas