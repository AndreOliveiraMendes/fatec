from typing import Literal

from flask import abort

from app.auxiliar.constant import Permission
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.models.usuarios import Usuarios


def check_own_reserva(reserva:Reservas_Auditorios, user:Usuarios):
    if user.id_pessoa != reserva.id_responsavel and not user.perm.has_any(Permission.ADMIN|Permission.AUTORIZAR):
        abort(403, description="Acesso negado à reserva de outro usuário.")

def check_role(user:Usuarios, action:Literal['CR', 'AR']):
    if action == 'CR' and not user.perm.has(Permission.ADMIN):
        abort(403, description="Acesso negado à atualização de reservas.")
    elif action == 'AR' and not user.perm.has_any(Permission.ADMIN|Permission.AUTORIZAR):
        abort(403, description="Acesso negado à autorização de reservas.")
