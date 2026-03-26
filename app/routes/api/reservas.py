from flask import Blueprint, jsonify

from app.decorators.decorators import admin_required

from .handler.handler_reservas import get_handler

bp = Blueprint('api_reservas', __name__, url_prefix='/api/reservas')

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

# checagem de conflitos
@bp.route('/check_conflict_reserva/<int:tipo_reserva>/<data:dia>/<int:id_aula>/<int:id_responsavel>')
def check_conflito_reserva(tipo_reserva, dia, id_aula, id_responsavel):
    return jsonify(get_handler(tipo_reserva, "check_conflict")(dia, id_aula, id_responsavel))