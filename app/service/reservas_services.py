from flask import abort
from sqlalchemy import func, select

from app.enums import StatusReservaAuditorioEnum
from app.extensions import db
from app.models.reservas.reservas_auditorios import Reservas_Auditorios


def check_unique_aprovada(reserva:Reservas_Auditorios):
    count_rtc = select(func.count()).select_from(Reservas_Auditorios).where(
        Reservas_Auditorios.id_reserva_auditorio != reserva.id_reserva_auditorio,
        Reservas_Auditorios.id_reserva_local == reserva.id_reserva_local,
        Reservas_Auditorios.id_reserva_aula == reserva.id_reserva_aula,
        Reservas_Auditorios.dia_reserva == reserva.dia_reserva,
        Reservas_Auditorios.status_reserva == StatusReservaAuditorioEnum.APROVADA
    )
    res = db.session.scalar(count_rtc)
    if res is None:
        res = 0
    if res > 0:
        abort(409, description="Já existe uma reserva aprovada para este auditório no mesmo horário.")