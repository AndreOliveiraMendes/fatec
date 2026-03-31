from app.auxiliar.general import none_if_empty


def get_equipamentos_from_form(form):
    equipamentos = []
    for key, value in form.items():
        if key.startswith('qtd'):
            equipamento_id = int(key[4:-1])
            quantidade = none_if_empty(value, int)
            if quantidade is not None and quantidade > 0:
                equipamentos.append((equipamento_id, quantidade))
    return equipamentos