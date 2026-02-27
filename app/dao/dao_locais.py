
from sqlalchemy import select

from app.enums import DisponibilidadeEnum, TipoLocalEnum
from app.extensions import db
from app.models.locais import Locais


def get_locais():
    sel_locais = select(Locais)
    return db.session.execute(sel_locais).scalars().all()

def get_laboratorios(ignorar_inativo=False):
    sel_laboratorios = select(Locais)
    filtro = [Locais.tipo == TipoLocalEnum.LABORATORIO]
    if not ignorar_inativo:
        filtro.append(Locais.disponibilidade == DisponibilidadeEnum.DISPONIVEL)
    sel_laboratorios = sel_laboratorios.where(*filtro)
    return db.session.execute(sel_laboratorios).scalars().all()

def get_auditorios():
    sel_auditorios = select(Locais)
    filtro = [
        Locais.tipo == TipoLocalEnum.AUDITORIO,
        Locais.disponibilidade == DisponibilidadeEnum.DISPONIVEL
    ]
    sel_auditorios = sel_auditorios.where(*filtro)
    return db.session.execute(sel_auditorios).scalars().all()