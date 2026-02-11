
from flask import Blueprint, Response

from app.auxiliar.auxiliar_api import (delete_reserva_fixa,
                                       delete_reserva_temporaria,
                                       get_reserva_fixa_indirect,
                                       get_reserva_fixa_info,
                                       get_reserva_temporaria_indirect,
                                       get_reserva_temporaria_info,
                                       update_reserva_fixa,
                                       update_reserva_temporaria)
from app.auxiliar.decorators import admin_required

bp = Blueprint('api_reservas', __name__, url_prefix='/api/reservas')

@bp.route('/reserva/<int:tipo_reserva>/info/<int:id_reserva>')
@admin_required
def get_reserva_info(tipo_reserva, id_reserva):
    if tipo_reserva == 0: # reserva fixa
        return get_reserva_fixa_info(id_reserva)
    elif tipo_reserva == 1: # reserva temporaria
        return get_reserva_temporaria_info(id_reserva)
    else:
        return Response(status=400)

@bp.route('/reserva/<int:tipo_reserva>/update/<int:id_reserva>', methods=['POST'])
@admin_required
def update_reserva(tipo_reserva, id_reserva):
    if tipo_reserva == 0: # reserva fixa
        return update_reserva_fixa(id_reserva)
    elif tipo_reserva == 1: # reserva temporaria
        return update_reserva_temporaria(id_reserva)
    else:
        return Response(status=400)

@bp.route('/reserva/<int:tipo_reserva>/delete/<int:id_reserva>', methods=['DELETE'])
@admin_required
def delete_reserva(tipo_reserva, id_reserva):
    if tipo_reserva == 0: # reserva fixa
        return delete_reserva_fixa(id_reserva)
    elif tipo_reserva == 1: # reserva temporaria
        return delete_reserva_temporaria(id_reserva)
    else:
        return Response(status=400)
    
# checagens de informações de reservas indiretamente pelo dia/horario/local
@bp.route('/get_reserva/<int:tipo_reserva>/<data:dia>/<int:id_local>/<int:id_aula>', methods=['GET'])
def get_reserva_indirect(tipo_reserva, dia, id_local, id_aula):
    if tipo_reserva == 0: # reserva fixa
        return get_reserva_fixa_indirect(dia, id_local, id_aula)
    elif tipo_reserva == 1: # reserva temporaria
        return get_reserva_temporaria_indirect(dia, id_local, id_aula)
    else:
        return Response(status=400)