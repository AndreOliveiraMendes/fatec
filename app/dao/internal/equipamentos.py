from sqlalchemy import select

from app.extensions import db
from app.models.equipamentos import Categorias_de_Equipamentos


def get_categorias():
    sel_categorias = select(Categorias_de_Equipamentos)
    return db.session.execute(sel_categorias).scalars().all()