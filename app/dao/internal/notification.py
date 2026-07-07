from sqlalchemy import select

from app.extensions import db
from app.models.notifications import (Reserva_Auditorio_Email,
                                      Reserva_Auditorio_Equipamentos)


def get_notificacoes_email():
    sel_notification = select(Reserva_Auditorio_Email)
    return db.session.execute(sel_notification).scalars().all()

def get_notificacoes_equipamentos():
    sel_notificacoes_equipamentos = select(Reserva_Auditorio_Equipamentos)
    return db.session.execute(sel_notificacoes_equipamentos).scalars().all()