from flask import Blueprint, jsonify, request
from sqlalchemy import select

from app.auxiliar.parsing import parse_date_string
from app.extensions import db
from app.models.reservas.reservas_auditorios import Reservas_Auditorios

bp = Blueprint('api_reservas_adutiorios', __name__, url_prefix='/api/reservas/auditorios')

@bp.route("/list")
def list():
    inicio = parse_date_string(request.args.get("inicio"))
    fim = parse_date_string(request.args.get("fim"))

    sel_res_aud = select(Reservas_Auditorios)


    if inicio:
        sel_res_aud = sel_res_aud.where(Reservas_Auditorios.dia_reserva >= inicio)
    if fim:
        sel_res_aud = sel_res_aud.where(Reservas_Auditorios.dia_reserva <= fim)

    reservas = db.session.execute(sel_res_aud).scalars().all()
    return jsonify([
        {
            "id": res.id_reserva_auditorio,
            "responsavel": res.responsavel.nome_pessoa,
            "data": res.dia_reserva.isoformat(),
            "horario_inicio": str(res.aula_ativa.aula.horario_inicio),
            "horario_fim": str(res.aula_ativa.aula.horario_fim),
            "horario": (
                f"{res.aula_ativa.aula.horario_inicio} - "
                f"{res.aula_ativa.aula.horario_fim}"
            )
        }
        for res in reservas
    ])