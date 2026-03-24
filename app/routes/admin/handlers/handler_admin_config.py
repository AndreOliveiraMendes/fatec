from app.dao.internal.equipamentos import get_equipamentos


def get_quantidades_equipamento_dia(dia):
    equipamentos = get_equipamentos()
    return {
        1:5,
        2:10
    }