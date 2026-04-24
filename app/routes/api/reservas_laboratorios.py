from flask import Blueprint, jsonify
from sqlalchemy import select

from app.decorators.decorators import admin_required
from app.enums import TipoLocalEnum
from app.extensions import db
from app.models.locais import Locais

from .handler.handler_reservas_laboratorios import get_handler

bp = Blueprint('api_reservas_laboratorio', __name__, url_prefix='/api/reservas')


@bp.route("/listar_laboratorios")
@admin_required
def api_get_laboratorios():
    sel_laboratorios = select(Locais).where(
        Locais.tipo == TipoLocalEnum.LABORATORIO
    )

    laboratorios = db.session.execute(sel_laboratorios).scalars().all()

    result_labs = []
    for laboratorio in laboratorios:
        res = {
            "id": laboratorio.id_local,
            "nome": laboratorio.nome_local,
            "disponivel": laboratorio.disponibilidade.value
        }
        result_labs.append(res)

    return jsonify(result_labs)

@bp.route('/reserva/<int:tipo_reserva>/info/<int:id_reserva>')
def get_reserva_info(tipo_reserva, id_reserva):
    return jsonify(get_handler(tipo_reserva, "info")(id_reserva))


@bp.route('/reserva/<int:tipo_reserva>/update/<int:id_reserva>', methods=['POST'])
@admin_required
def update_reserva(tipo_reserva, id_reserva):
    result, code = get_handler(tipo_reserva, "update")(id_reserva)
    return jsonify(result), code


@bp.route('/reserva/<int:tipo_reserva>/delete/<int:id_reserva>', methods=['DELETE'])
@admin_required
def delete_reserva(tipo_reserva, id_reserva):
    result, code = get_handler(tipo_reserva, "delete")(id_reserva)
    return jsonify(result), code


# checagem indireta por dia/local/aula
@bp.route('/get_reserva/<int:tipo_reserva>/<data:dia>/<int:id_local>/<int:id_aula>')
def get_reserva_indirect(tipo_reserva, dia, id_local, id_aula):
    result = get_handler(tipo_reserva, "indirect")(dia, id_local, id_aula)
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result)

# checagem de conflitos
@bp.route('/check_conflict_reserva/<int:tipo_reserva>/<data:dia>/<int:id_aula>/<int:id_responsavel>')
def check_conflito_reserva(tipo_reserva, dia, id_aula, id_responsavel):
    return jsonify(get_handler(tipo_reserva, "check_conflict")(dia, id_aula, id_responsavel))