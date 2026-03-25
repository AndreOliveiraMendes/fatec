from app.dao.internal.controle import get_equipamento_disponibilidade_dia

def get_quantidades_equipamento_dia(dia, id = None):
    return get_equipamento_disponibilidade_dia(dia, id)

def ajuste_quantidade(id, quantidade, dia):
    pass