from typing import Literal

from flask import abort
from sqlalchemy import func, select

from app.auxiliar.constant import Permission
from app.enums import StatusReservaAuditorioEnum
from app.extensions import db
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.models.usuarios import Usuarios


def check_own_reserva(reserva:Reservas_Auditorios, user:Usuarios):
    if user.id_pessoa != reserva.id_responsavel and user.perm & (Permission.ADMIN+Permission.AUTORIZAR) == 0:
        abort(403, description="Acesso negado à reserva de outro usuário.")

def check_role(user:Usuarios, action:Literal['CR', 'AR']):
    if action == 'CR' and user.perm & Permission.ADMIN == 0:
        abort(403, description="Acesso negado à atualização de reservas.")
    elif action == 'AR' and user.perm & (Permission.ADMIN+Permission.AUTORIZAR) == 0:
        abort(403, description="Acesso negado à autorização de reservas.")

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