import csv
from io import StringIO

from flask import (Blueprint, Response, abort, g, jsonify, render_template,
                   request)

from app.auxiliar.general import formatar_valor
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.historicos import Historicos
from app.routes_helper.controller import get_controller
from app.routes_helper.ui import disable_action, include_action
from config.general import LOCAL_TIMEZONE

from .handlers import dispatcher, get_data
from .states import VALID_STATES

bp = Blueprint('database_historicos', __name__, url_prefix="/database")

@bp.route("/historicos", methods=["GET", "POST"])
@admin_required
@crud_route()
def gerenciar_historicos():
    disabled = ['inserir', 'editar', 'excluir']
    include = [{'label':"Exportar", 'value':"exportar", 'icon':"glyphicon-download"}]
    disable_action(g.extras, disabled)
    include_action(g.extras, include)
    user_agent = request.headers.get('User-Agent')
    is_mobile = 'Mobile' in user_agent if user_agent else False
    g.extras['is_mobile'] = is_mobile
    field = [
        ('ID', 'visible-md visible-lg'),
        ('Usuário', 'visible-md visible-lg'),
        'Tabela',
        'Categoria',
        'Data/Hora',
        'Mensagem',
        ('Chave Primária', 'visible-md visible-lg'),
        ('Origem', 'visible-md visible-lg'),
        ('Observação', 'visible-md visible-lg')
    ]
    if is_mobile:
        field = field[2:6]
    g.extras['field'] = field
    if request.method == 'POST':
        get_controller(VALID_STATES, dispatcher, g.acao, g.bloco)

    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/historicos.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)

@bp.route("/historicos/exportar", methods=['POST'])
def exportar_historicos():
    data_filter, sel_historicos, _ = get_data()
    if data_filter:
        sel_historicos = sel_historicos.where(*data_filter)
    formato = request.form.get('formato', 'csv')
    header = [c.name for c in Historicos.__table__.columns]
    resultados = db.session.execute(sel_historicos).scalars().all()
    for row in resultados:
        row.data_hora = row.data_hora.replace(tzinfo=LOCAL_TIMEZONE)
    if formato == 'csv':
        utf8_bom = '\ufeff'
        si = StringIO()
        si.write(utf8_bom)
        writer = csv.writer(si)
        writer.writerow(header)
        for row in resultados:
            writer.writerow([getattr(row, col) for col in header])
        output = si.getvalue()
        si.close()
        return Response(
            output,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment;filename=Historico.csv"}
        )
    elif formato == 'json':
        data = [
            {col: formatar_valor(getattr(row, col)) for col in header}
            for row in resultados
        ]
        return jsonify(data)
    else:
        abort(400, description="Formato inválido")