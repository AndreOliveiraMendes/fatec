from flask import Blueprint, jsonify, request

from app.decorators.decorators import admin_required
from app.enums import StatusReservaEquipamentoEnum
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos
from app.routes.api.handler.handler_reservas_equipamentos import (
    aprovar_reserva_equipamento_handler, build_detalhes_reserva,
    cancelar_reserva_equipamento_handler, check_cancelamento_permissao,
    finalizar_reserva_se_concluida, get_item_reserva,
    registrar_devolucao_equipamento_handler)

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

    if not data or not "motivo" in data:
        return jsonify({'error': 'Campo "motivo" é obrigatório para cancelar a reserva'}), 400

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
    reserva = db.session.get(Reservas_Equipamentos, id_reserva)
    if not reserva:
        return jsonify({'error': 'Reserva não encontrada'}), 404
    
    code, msg = aprovar_reserva_equipamento_handler(reserva)

    if code != 200:
        return jsonify({'error': msg}), code
    else:
        return jsonify({'ok': True})
    
@bp.route('/<int:id_reserva>/devolucoes/<int:id_equipamento>/gerenciar', methods=['POST'])
@admin_required
def registrar_devolucao_equipamento(id_reserva, id_equipamento):
    reserva = db.session.get(Reservas_Equipamentos, id_reserva)
    if not reserva:
        return jsonify({'error': 'Reserva não encontrada'}), 404
    
    if not reserva.status_reserva == StatusReservaEquipamentoEnum.ATIVA:
        return jsonify({'error': 'Apenas reservas ativas podem ser gerenciadas'}), 400
    
    item = get_item_reserva(id_reserva, id_equipamento)
    if not item:
        return jsonify({'error': 'Equipamento não encontrado nesta reserva'}), 404
    
    data = request.get_json()

    if not data or "devolvido" not in data:
        return jsonify({'error': 'Campo "devolvido" é obrigatório'}), 400
    
    qtd_devolvido = data.get("devolvido")

    if not isinstance(qtd_devolvido, int) or qtd_devolvido < 0 or qtd_devolvido > item.quantidade:
        return jsonify({'error': f'Campo "devolvido" deve ser um inteiro entre 0 e {item.quantidade}'}), 400
    
    code, msg = registrar_devolucao_equipamento_handler(item, qtd_devolvido)

    if code != 200:
        return jsonify({'error': msg}), code
    
    code, msg = finalizar_reserva_se_concluida(reserva)

    if code != 200:
        return jsonify({'error': msg}), code
    else:
        return jsonify({'ok': True, 'reserva_concluida': reserva.status_reserva == StatusReservaEquipamentoEnum.CONCLUIDA})