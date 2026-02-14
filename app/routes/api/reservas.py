from flask import Blueprint, abort

from app.auxiliar.auxiliar_api import (
    delete_reserva_fixa,
    delete_reserva_temporaria,
    get_reserva_fixa_indirect,
    get_reserva_fixa_info,
    get_reserva_temporaria_indirect,
    get_reserva_temporaria_info,
    update_reserva_fixa,
    update_reserva_temporaria
)

from app.auxiliar.decorators import admin_required

bp = Blueprint('api_reservas', __name__, url_prefix='/api/reservas')

# -------------------------
# MAPEAMENTO DE TIPOS
# -------------------------
RESERVA_HANDLERS = {
    0: {
        "info": get_reserva_fixa_info,
        "update": update_reserva_fixa,
        "delete": delete_reserva_fixa,
        "indirect": get_reserva_fixa_indirect
    },
    1: {
        "info": get_reserva_temporaria_info,
        "update": update_reserva_temporaria,
        "delete": delete_reserva_temporaria,
        "indirect": get_reserva_temporaria_indirect
    }
}

def get_handler(tipo_reserva: int, action: str):
    handler = RESERVA_HANDLERS.get(tipo_reserva, {}).get(action)
    if not handler:
        abort(400, description="Tipo de reserva inválido")
    return handler


# -------------------------
# ROTAS
# -------------------------

@bp.route('/reserva/<int:tipo_reserva>/info/<int:id_reserva>')
def get_reserva_info(tipo_reserva, id_reserva):
    return get_handler(tipo_reserva, "info")(id_reserva)


@bp.route('/reserva/<int:tipo_reserva>/update/<int:id_reserva>', methods=['POST'])
@admin_required
def update_reserva(tipo_reserva, id_reserva):
    return get_handler(tipo_reserva, "update")(id_reserva)


@bp.route('/reserva/<int:tipo_reserva>/delete/<int:id_reserva>', methods=['DELETE'])
@admin_required
def delete_reserva(tipo_reserva, id_reserva):
    return get_handler(tipo_reserva, "delete")(id_reserva)


# checagem indireta por dia/local/aula
@bp.route('/get_reserva/<int:tipo_reserva>/<data:dia>/<int:id_local>/<int:id_aula>')
def get_reserva_indirect(tipo_reserva, dia, id_local, id_aula):
    return get_handler(tipo_reserva, "indirect")(dia, id_local, id_aula)