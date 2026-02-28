def builder_helper_fixa(extras, info):
    aulas = set()
    semanas = set()
    row = {}

    for aula_ativa, aula, semana in info:
        aulas.add(aula)
        semanas.add(semana)
        row[(aula.id_aula, semana.id_semana)] = aula_ativa.id_aula_ativa

    extras['head'] = sorted(semanas, key=lambda s: s.id_semana)
    extras['first_col'] = sorted(aulas, key=lambda a: a.horario_inicio)
    extras['row'] = row

def builder_helper_temporaria(extras, aulas):
    table_aulas = []
    table_dias = []

    for info in aulas:
        par = (info.horario_inicio, info.horario_fim)
        if par not in table_aulas:
            table_aulas.append(par)

    table_aulas.sort(key=lambda e: e[0])
    size = len(table_aulas)

    for info in aulas:
        dia = info.dia_consulta
        semana = info.nome_semana

        for i, v in enumerate(table_dias):
            if v['dia'] == dia:
                index_dia = i
                break
        else:
            table_dias.append({'dia': dia, 'semana': semana, 'infos': [None]*size})
            index_dia = len(table_dias) - 1

        for i, v in enumerate(table_aulas):
            if info.horario_inicio == v[0] and info.horario_fim == v[1]:
                table_dias[index_dia]['infos'][i] = info
                break

    extras['head'] = table_aulas
    extras['dias'] = table_dias