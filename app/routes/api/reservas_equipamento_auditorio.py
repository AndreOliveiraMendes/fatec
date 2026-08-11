from flask import Blueprint, jsonify
from sqlalchemy import select

from app.extensions import db
from app.models.notifications import Reserva_Auditorio_Equipamentos

bp = Blueprint('api_relacoes_equipamento_auditorio', __name__, url_prefix='/api/reservas/relacoes_equipamento_auditorio')

@bp.route('/listar/<int:id_reserva_auditorio>', methods=['GET'])
def listar_relacoes_equipamento_auditorio(id_reserva_auditorio):
    stmt = select(Reserva_Auditorio_Equipamentos).where(Reserva_Auditorio_Equipamentos.id_reserva_auditorio == id_reserva_auditorio)
    relacoes = db.session.execute(stmt).scalars().all()
    relacoes_list = [
        {
            'id': relacao.id_item,
            'id_auditorio': relacao.id_reserva_auditorio,
            'id_equipamento': relacao.id_equipamento,
            'nome_equipamento': relacao.equipamento.nome_equipamento,
            'quantidade': relacao.quantidade,
            'observacoes': relacao.observacoes
        }
        for relacao in relacoes
    ]
    return jsonify({
        "equipamentos":relacoes_list,
        "reserva_auditorio": id_reserva_auditorio   
        }
    )