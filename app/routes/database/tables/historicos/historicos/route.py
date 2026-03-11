import csv
from io import StringIO

from flask import (Blueprint, Response, abort, flash, g, jsonify,
                   render_template, request)
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import between, func, or_, select

from app.auxiliar.general import formatar_valor, none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_datetime_string
from app.dao.internal.usuarios import get_usuarios
from app.decorators.decorators import admin_required, crud_route
from app.enums import OrigemEnum
from app.extensions import db
from app.models.historicos import Historicos
from app.routes_helper.request import get_query_params
from app.routes_helper.ui import disable_action, include_action
from config.general import LOCAL_TIMEZONE, PER_PAGE

#from .handlers import dispatcher
#from .states import VALID_STATES

bp = Blueprint('database_historicos', __name__, url_prefix="/database")

def get_tabelas():
    sel_tabelas = select(Historicos.tabela).distinct()
    return db.session.execute(sel_tabelas).all()

def get_categorias():
    sel_categorias = select(Historicos.categoria).distinct()
    return db.session.execute(sel_categorias).all()

def get_origens():
    sel_origens = select(Historicos.origem).distinct()
    return db.session.execute(sel_origens).all()

def filtro_intervalo(inicio_procura, fim_procura):
    if inicio_procura and fim_procura:
        return between(Historicos.data_hora, inicio_procura, fim_procura)
    elif inicio_procura:
        return inicio_procura <= Historicos.data_hora
    elif fim_procura:
        return fim_procura >= Historicos.data_hora
    else:
        raise ValueError("Especifique ao menos um valor")
    
def get_conteudo(conteudo):
    return or_(
        Historicos.message.ilike(f"%{conteudo}%"),
        Historicos.chave_primaria.ilike(f"%{conteudo}%"),
        Historicos.observacao.ilike(f"%{conteudo}%")
    )

def get_data():
    id_historico = none_if_empty(request.form.get('id_historico'), int)
    id_usuario = none_if_empty(request.form.get('id_usuario'), int)
    tabela = none_if_empty(request.form.get('tabela'))
    categoria = none_if_empty(request.form.get('categoria'))
    inicio_procura = parse_datetime_string(request.form.get('inicio_procura'))
    fim_procura = parse_datetime_string(request.form.get('fim_procura'))
    origem = none_if_empty(request.form.get('origem'))
    conteudo = none_if_empty(request.form.get('conteudo'))
    filters = []
    query_params = get_query_params(request)
    if id_historico is not None:
        filters.append(Historicos.id_historico == id_historico)
    if id_usuario is not None:
        filters.append(Historicos.id_usuario == id_usuario)
    if tabela:
        filters.append(Historicos.tabela == tabela)
    if categoria:
        filters.append(Historicos.categoria == categoria)
    if inicio_procura or fim_procura:
        filters.append(filtro_intervalo(inicio_procura, fim_procura))
    if origem:
        filters.append(Historicos.origem == OrigemEnum(origem))
    if conteudo:
        filters.append(get_conteudo(conteudo))
    sel_historicos = select(Historicos)
    return filters, sel_historicos, query_params

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
    if request.method == 'POST':
        if g.acao in disabled:
            abort(403, description="Esta funcionalidade não foi implementada.")
        if g.acao == 'listar':
            sel_historicos = select(Historicos)
            historicos_paginados = SelectPagination(
                select=sel_historicos, session=db.session, page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['historicos'] = historicos_paginados.items
            g.extras['pagination'] = historicos_paginados

        if g.acao in ['procurar', 'exportar'] and g.bloco == 0:
            g.extras['usuarios'] = get_usuarios()
            g.extras['tabelas'] = get_tabelas()
            g.extras['categorias'] = get_categorias()
            g.extras['origens'] = get_origens()
        elif g.acao == 'procurar' and g.bloco == 1:
            data_filter, sel_historicos, query_params = get_data()
            if data_filter:
                sel_historicos = sel_historicos.where(*data_filter)
                historicos_paginados = SelectPagination(
                    select=sel_historicos, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['historicos'] = historicos_paginados.items
                g.extras['pagination'] = historicos_paginados
                g.extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo:", "danger")
                g.redirect_action, g.bloco = register_return(
                    g.url, g.acao, g.extras,
                    usuarios=get_usuarios(), tabelas=get_tabelas(), categorias=get_categorias(),
                    origens=get_origens()
                )
        elif g.acao == 'exportar' and g.bloco == 1:
            data_filter, sel_historicos, query_params = get_data()
            if data_filter:
                sel_historicos = sel_historicos.where(*data_filter)
            sel_count_historicos = (
                select(func.count())
                .select_from(sel_historicos.subquery())
            )
            g.extras['count'] = db.session.execute(sel_count_historicos).scalar()
            g.extras['query_params'] = query_params
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/historicos.html",
        user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)

@bp.route("/historicos/exportar", methods=['POST'])
def exportar_historicos():
    data_filter, sel_historicos, query_params = get_data()
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