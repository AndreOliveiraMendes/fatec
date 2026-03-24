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

def merge_aulas(modo, aulas, labs, dia, tela):
    if modo == 'multiplo':
        horarios = []
        for aula in aulas:
            if horarios:
                horario = horarios[-1]
                id_aula_1 = horario[-1][0].id_aula_ativa
                id_aula_2 = aula[0].id_aula_ativa
                can_merge = all(get_reserva(lab.id_local, id_aula_1, dia, True, True, tela) == get_reserva(lab.id_local, id_aula_2, dia, True, True, tela) for lab in labs) \
                    and horario[-1][1].horario_fim == aula[1].horario_inicio
                if can_merge:
                    horarios[-1].append(aula)
                else:
                    horarios.append([aula])
            else:
                horarios.append([aula])
        return horarios
    return aulas