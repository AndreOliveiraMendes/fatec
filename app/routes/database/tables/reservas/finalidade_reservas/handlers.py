import json

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.reservas.reservas_laboratorios import Finalidade_Reserva
from app.routes_helper.db_actions import db_action
from config.general import PER_PAGE


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