import json
from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.reservas import get_finalidade_reserva
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.reservas.reservas_laboratorios import Finalidade_Reserva
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE, str_to_bool

dispatcher = {}
ALLOWED_KEYS = {"template", "show_status", "use_description"}

def validate_config(config):
    if config is None:
        return True, None

    if not isinstance(config, dict):
        return False, "Config deve ser um objeto JSON"

    clean = {}

    for k, v in config.items():
        if k not in ALLOWED_KEYS:
            return False, f"Chave inválida: {k}"

        if k == "template":
            if not isinstance(v, str):
                return False, "template deve ser string"
            clean[k] = v

        elif k in ("show_status", "use_description"):
            if not isinstance(v, bool):
                return False, f"{k} deve ser boolean"
            clean[k] = v

    return True, clean

def build_config_from_form(request):
    config = {}

    template = request.form.get("config_template")
    show_status = str_to_bool(request.form.get("config_show_status"))
    use_description = str_to_bool(request.form.get("config_use_description"))

    if template:
        config["template"] = template

    if show_status is not None:
        config["show_status"] = show_status

    if use_description is not None:
        config["use_description"] = use_description

    # override por JSON bruto
    raw = request.form.get("config_raw")
    erro = ""

    if raw:
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as e:
            erro = f"JSON inválido: {e}"
            config = None

    if not erro:
        valid, config = validate_config(config)

    if not valid:
        erro = config

    return config, erro

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
    use_description = none_if_empty(request.form.get('config_use_description'), str_to_bool)
    show_status = none_if_empty(request.form.get('config_show_status'), str_to_bool)

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
            Finalidade_Reserva.config["template"].as_string().ilike(f"%{template}%")
        )
    if use_description is not None:
        filters.append(
            Finalidade_Reserva.config["use_description"].as_boolean() == use_description
        )
    if show_status is not None:
        filters.append(
            Finalidade_Reserva.config["show_status"].as_boolean() == show_status
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
    config, error = build_config_from_form(request)
            
    if error:
        flash(error, "danger")
    else:
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
    config, error = build_config_from_form(request)
    if error:
        flash(error, "danger")
    else:
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