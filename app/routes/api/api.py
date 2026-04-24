from datetime import date, timedelta

from flask import Blueprint, jsonify
from sqlalchemy import func, select

from app.enums import StatusReservaEquipamentoEnum
from app.extensions import db
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos

bp = Blueprint('api', __name__, url_prefix='/api')

def format_data(d):
    hoje = date.today()
    if d == hoje:
        return f"Hoje ({d.strftime('%d/%m')})"
    elif d == hoje + timedelta(days=1):
        return f"Amanhã ({d.strftime('%d/%m')})"
    elif d == hoje - timedelta(days=1):
        return f"Ontem ({d.strftime('%d/%m')})"
    return d.strftime('%d/%m/%Y')

@bp.route("/notification/reservas")
def get_reservas_equipamentos():
    stmt = (
        select(
            Reservas_Equipamentos.data_reserva,
            func.count().label("total")
        )
        .where(
            Reservas_Equipamentos.status_reserva.in_([
                StatusReservaEquipamentoEnum.PENDENTE,
                StatusReservaEquipamentoEnum.ATIVA
            ])
        )
        .group_by(Reservas_Equipamentos.data_reserva)
        .order_by(Reservas_Equipamentos.data_reserva)
    )

    rows = db.session.execute(stmt).all()

    data = {
        "count": sum(r.total for r in rows),
        "list": [
            f"{format_data(r.data_reserva)} ({r.total})"
            for r in rows
        ]
    }

    return jsonify(data)