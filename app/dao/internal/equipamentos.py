from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.equipamentos import Categorias_de_Equipamentos, Equipamentos


def get_categorias():
    sel_categorias = select(Categorias_de_Equipamentos)
    return db.session.execute(sel_categorias).scalars().all()

def get_equipamentos(load_categoria = False):
    sel_equipamentos = select(Equipamentos)
    if load_categoria:
        sel_equipamentos = sel_equipamentos.options(
            joinedload(Equipamentos.categoria)
        )
    return db.session.execute(sel_equipamentos).scalars().all()