from app.auxiliar.general import none_if_empty


def get_equipamentos_from_form(form):
    equipamentos = {}
    for key, value in form.items():
        print(key)
        if key.startswith('qtd') and key.endswith(']'):
            equipamento_id = int(key[4:-1])
            quantidade = none_if_empty(value, int)
            if quantidade is not None and quantidade > 0:
                equipamentos[equipamento_id] = equipamentos.get(equipamento_id, {})
                equipamentos[equipamento_id]['qtd'] = quantidade
        if key.startswith('obs') and key.endswith(']'):
            equipamento_id = int(key[4:-1])
            obs = none_if_empty(value)
            if obs:
                equipamentos[equipamento_id] = equipamentos.get(equipamento_id, {})
                equipamentos[equipamento_id]['obs'] = obs
    return equipamentos