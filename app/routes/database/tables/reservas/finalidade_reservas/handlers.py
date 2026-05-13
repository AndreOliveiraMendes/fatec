import json
from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import func, select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.reservas import get_finalidade_reserva
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.reservas.reservas_laboratorios import Finalidade_Reserva
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE, str_to_bool, str_to_bool_json

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def listar_handler():
    sel_finalidades = select(Finalidade_Reserva)
    finalidade_reservas_paginada = SelectPagination(
        select=sel_finalidades, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['finalidades'] = finalidade_reservas_paginada.items
    g.extras['pagination'] = finalidade_reservas_paginada

@register_handler(dispatcher, 'procurar', 1)
def search_handler():
    id_finalidade = none_if_empty(request.form.get('id_finalidade'), int)
    nome = none_if_empty(request.form.get('nome'))
    ativo = none_if_empty(request.form.get('ativo'), str_to_bool)
    descricao = none_if_empty(request.form.get('descricao'))
    template = none_if_empty(request.form.get('config_template'))
    use_description = none_if_empty(request.form.get('config_use_description'), str_to_bool_json)
    show_status = none_if_empty(request.form.get('config_show_status'), str_to_bool_json)

    filters = []
    query_params = get_query_params(request)
    if id_finalidade is not None:
        filters.append(Finalidade_Reserva.id_finalidade == id_finalidade)
    if nome:
        filters.append(Finalidade_Reserva.nome.ilike(f"%{nome}%"))
    if ativo is not None:
        filters.append(Finalidade_Reserva.ativo == ativo)
    if descricao:
        filters.append(Finalidade_Reserva.descricao.ilike(f"%{descricao}%"))
    if template:
        filters.append(
            func.JSON_UNQUOTE(
                func.JSON_EXTRACT(Finalidade_Reserva.config, '$.template')
            ).ilike(f"%{template}%")
        )
    if use_description is not None:
        filters.append(
            func.JSON_UNQUOTE(
                func.JSON_EXTRACT(Finalidade_Reserva.config, '$.use_description')
            ) == use_description
        )
    if show_status is not None:
        filters.append(
            func.JSON_UNQUOTE(
                func.JSON_EXTRACT(Finalidade_Reserva.config, '$.show_status')
            ) == show_status
        )
    if filters:
        sel_finalidades = select(Finalidade_Reserva).where(*filters)
        finalidade_reservas_paginada = SelectPagination(
            select=sel_finalidades, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['finalidades'] = finalidade_reservas_paginada.items
        g.extras['pagination'] = finalidade_reservas_paginada
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(g.url, g.acao, g.extras)

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    nome = none_if_empty(request.form.get("nome"))
    ativo = none_if_empty(request.form.get("ativo"), bool)
    descricao = none_if_empty(request.form.get("descricao"))
    config_str = none_if_empty(request.form.get("config"))
    config = None
    valid = True
    if config_str:
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError as e:
            valid = False
            flash(f"JSON inválido: {str(e)}", "danger")
            
    if valid:
        nova_finalidade = Finalidade_Reserva(
            nome = nome,
            ativo = ativo,
            descricao = descricao,
            config = config
        )

        db_action(
            "Inserção",
            "Finalidade da reserva cadastrada com sucesso",
            "Erro ao cadastrar finalidade",
            obj=nova_finalidade
        )
    else:
        flash("JSON inválido. Verifique a formatação e tente novamente.", "danger")

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def finalidade_prefetch():
    g.extras['finalidades'] = get_finalidade_reserva()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def finalidade_fetch():
    id_finalidade = none_if_empty(request.form.get('id_finalidade'), int)

    finalidade = db.get_or_404(Finalidade_Reserva, id_finalidade)
    g.extras['finalidade'] = finalidade

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_finalidade = none_if_empty(request.form.get('id_finalidade'), int)
    nome = none_if_empty(request.form.get("nome"))
    ativo = none_if_empty(request.form.get("ativo"), bool)
    descricao = none_if_empty(request.form.get("descricao"))
    config_str = none_if_empty(request.form.get("config"))
    config = None
    valid = True
    if config_str:
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError as e:
            valid = False
            flash(f"JSON inválido: {str(e)}", "danger")
    if valid:
        finalidade = db.get_or_404(Finalidade_Reserva, id_finalidade)
        dados_anteriores = copy(finalidade)

        def update():
            finalidade.nome = nome
            finalidade.ativo = ativo
            finalidade.descricao = descricao
            finalidade.config = config

        db_action(
            "Edição",
            "Finalidade editada com sucesso",
            "Erro ao editar finalidade",
            obj=finalidade,
            old_obj=dados_anteriores,
            action=update
        )

    else:
        flash("JSON inválido. Verifique a formatação e tente novamente.", "danger")

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        finalidades=get_finalidade_reserva()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_finalidade = none_if_empty(request.form.get('id_finalidade'), int)

    finalidade = db.get_or_404(Finalidade_Reserva, id_finalidade)

    db_action(
        "Exclusão",
        "Finalidade excluida com sucesso",
        "Erro ao excluir finalidade",
        obj=finalidade
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        finalidades=get_finalidade_reserva()
    )