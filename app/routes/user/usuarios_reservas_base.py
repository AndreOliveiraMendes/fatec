from flask import Blueprint

from app.decorators.decorators import login_required
from app.routes.user.handler.handler_reserva import (cancelar_reserva_generico,
                                                     editar_reserva_generico,
                                                     resolve_tipo)

bp = Blueprint('usuarios_reservas_base', __name__, url_prefix='/usuario')

@bp.route("/get_info/<tipo_reserva>/<int:id_reserva>")
@login_required
def get_info_reserva(tipo_reserva, id_reserva):
    tipo = resolve_tipo(tipo_reserva)
    return tipo["info"](id_reserva)

@bp.route("/cancelar_reserva/<tipo_reserva>/<int:id_reserva>", methods=['POST'])
@login_required
def cancelar_reserva(tipo_reserva, id_reserva):
    tipo = resolve_tipo(tipo_reserva)

    return cancelar_reserva_generico(
        tipo["model"],
        id_reserva,
        tipo["redirect"]()
    )

@bp.route("/editar_reservas/<tipo_reserva>/<int:id_reserva>", methods=['POST'])
@login_required
def editar_reserva(tipo_reserva, id_reserva):
    tipo = resolve_tipo(tipo_reserva)

    return editar_reserva_generico(
        tipo["model"],
        id_reserva,
        tipo["redirect"]()
    )