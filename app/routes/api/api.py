
from flask import Blueprint, jsonify
from sqlalchemy import select

from app.auxiliar.decorators import admin_required
from app.models import Locais, TipoLocalEnum, db

bp = Blueprint('api', __name__, url_prefix='/api')

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