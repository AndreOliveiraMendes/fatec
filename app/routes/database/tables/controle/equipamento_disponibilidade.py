
import copy

from flask import Blueprint, flash, g, render_template, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.controle import get_equipamento_disponibilidades
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.decorators.decorators import admin_required, crud_route
from app.extensions import db
from app.models.controle import EquipamentoDisponibilidade
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

bp = Blueprint('database_equipamentos_disponibilidade', __name__, url_prefix="/database")

@bp.route('/equipamentos_disponibilidade', methods=['GET', 'POST'])
@admin_required
@crud_route()
def gerenciar_equipamentos_disponibilidade():
    if request.method == 'POST':
        if g.acao == "listar":
            sel_disponibilidade = select(EquipamentoDisponibilidade)
            disponibilidade_paginada = SelectPagination(
                select=sel_disponibilidade, session=db.session,
                page=g.page, per_page=PER_PAGE, error_out=False
            )
            g.extras['disponibilidades'] = disponibilidade_paginada.items
            g.extras['pagination'] = disponibilidade_paginada

        elif g.acao == "procurar" and g.bloco == 0:
            g.extras["equipamentos"] = get_equipamentos()
        elif g.acao == "procurar" and g.bloco == 1:
            id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)
            equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            data_start = parse_date_string(request.form.get('data_start'))
            data_end = parse_date_string(request.form.get('data_end'))
            quantidade_min = none_if_empty(request.form.get('quantidade_min'), int)
            quantidade_max = none_if_empty(request.form.get('quantidade_max'), int)

            filters = []
            query_params = get_query_params(request)
            if id_disponibilidade is not None:
                filters.append(EquipamentoDisponibilidade.id_disponibilidade == id_disponibilidade)
            if equipamento is not None:
                filters.append(EquipamentoDisponibilidade.id_equipamento == equipamento)
            if data_start:
                filters.append(EquipamentoDisponibilidade.data >= data_start)
            if data_end:
                filters.append(EquipamentoDisponibilidade.data <= data_end)
            if quantidade_min:
                filters.append(EquipamentoDisponibilidade.quantidade_total >= quantidade_min)
            if quantidade_max:
                filters.append(EquipamentoDisponibilidade.quantidade_total <= quantidade_max)
            if filters:
                sel_disponibilidade = select(EquipamentoDisponibilidade).where(
                    *filters
                )
                disponibilidade_paginada = SelectPagination(
                    select=sel_disponibilidade, session=db.session,
                    page=g.page, per_page=PER_PAGE, error_out=False
                )
                g.extras['disponibilidades'] = disponibilidade_paginada.items
                g.extras['pagination'] = disponibilidade_paginada
                g.extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                g.redirect_action, g.bloco = register_return(
                    g.url, g.acao, g.extras,
                    equipamentos = get_equipamentos()
                )

        elif g.acao == "inserir" and g.bloco == 0:
            g.extras["equipamentos"] = get_equipamentos()
        elif g.acao == "inserir" and g.bloco == 1:
            id_equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            data = parse_date_string(request.form.get('data'))
            quantidade_total = none_if_empty(request.form.get('quantidade_total'), int)

            try:
                novo_registro_disponibilidade = EquipamentoDisponibilidade(
                    id_equipamento = id_equipamento,
                    data = data,
                    quantidade_total = quantidade_total
                )
                db.session.add(novo_registro_disponibilidade)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Inserção', novo_registro_disponibilidade)

                db.session.commit()
                flash("Disponibilidade criada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao criar disponibilidade")
            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, equipamentos=get_equipamentos()
            )

        elif g.acao in ["editar", "excluir"] and g.bloco == 0:
            g.extras['disponibilidades'] = get_equipamento_disponibilidades()
        elif g.acao in ["editar", "excluir"] and g.bloco == 1:
            id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)
            disponibilidade = db.get_or_404(EquipamentoDisponibilidade, id_disponibilidade)
            g.extras['disponibilidade'] = disponibilidade
            g.extras['equipamentos'] = get_equipamentos()

        elif g.acao == "editar" and g.bloco == 2:
            id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)
            equipamento = none_if_empty(request.form.get('id_equipamento'), int)
            data = parse_date_string(request.form.get('data'))
            quantidade_total = none_if_empty(request.form.get('quantidade_total'), int)

            disponibilidade = db.get_or_404(EquipamentoDisponibilidade, id_disponibilidade)
            try:
                dados_anteriores = copy.copy(disponibilidade)
                disponibilidade.id_equipamento = equipamento
                disponibilidade.data = data
                disponibilidade.quantidade_total = quantidade_total

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Edição', disponibilidade, dados_anteriores)

                db.session.commit()
                flash("Disponibilidade editada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao editar disponilidade")
            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, disponibilidades = get_equipamento_disponibilidades()
            )

        elif g.acao == "excluir" and g.bloco == 2:
            id_disponibilidade = none_if_empty(request.form.get('id_disponibilidade'), int)

            disponibilidade = db.get_or_404(EquipamentoDisponibilidade, id_disponibilidade)
            try:
                db.session.delete(disponibilidade)

                db.session.flush()
                registrar_log_generico_usuario(g.userid, 'Exclusão', disponibilidade)

                db.session.commit()
                flash("Disponibilidade excluida com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao excluir disponibilidade")
            g.redirect_action, g.bloco = register_return(
                g.url, g.acao, g.extras, disponibilidades = get_equipamento_disponibilidades()
            )
    if g.redirect_action:
        return g.redirect_action
    return render_template("database/table/equipamentos_disponibilidade.html", user=g.user, acao=g.acao, bloco=g.bloco, **g.extras)