import json

from flask import flash, g, request

from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.decorators.decorators import register_handler
from app.models.reservas.reservas_laboratorios import Finalidade_Reserva
from app.routes_helper.db_actions import db_action


dispatcher = {}

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