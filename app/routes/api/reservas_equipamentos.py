from flask import Blueprint, jsonify, request

from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos
from app.routes.api.handler.handler_reservas_equipamentos import (
    build_detalhes_reserva, cancelar_reserva_equipamento_handler, check_cancelamento_permissao)

bp = Blueprint('api_reservas_equipamentos', __name__, url_prefix='/api/reservas/equipamentos')

@bp.route('/<int:id_reserva>/detalhes')
def detalhes_reserva_equipamento(id_reserva):
    reserva = db.session.get(Reservas_Equipamentos, id_reserva)
    if not reserva:
        return jsonify({'error': 'Reserva não encontrada'}), 404
    return jsonify(build_detalhes_reserva(reserva))

@bp.route('/<int:id_reserva>/cancelar', methods=['POST'])
def cancelar_reserva_equipamento(id_reserva):
    data = request.get_json()
    motivo = data.get("motivo")

    reserva = db.session.get(Reservas_Equipamentos, id_reserva)
    if not reserva:
        return jsonify({'error': 'Reserva não encontrada'}), 404
    
    if not check_cancelamento_permissao(reserva):
        return jsonify({'error': 'Permissão negada para cancelar esta reserva'}), 403
    
    code, msg = cancelar_reserva_equipamento_handler(reserva, motivo)

    if code != 200:
        return jsonify({'error': msg}), code
    else:
        return jsonify({'ok': True})
    
@bp.route('/<int:id_reserva>/aprovar', methods=['POST'])
@admin_required
def aprovar_reserva_equipamento(id_reserva):
    pass