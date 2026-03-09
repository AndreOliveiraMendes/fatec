from typing import Any

from flask import Blueprint, flash, render_template, request, session
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import or_, select

from app.auxiliar.constant import DB_ERRORS
from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.auxiliar.parsing import parse_date_string
from app.dao.internal.equipamentos import get_equipamentos
from app.dao.internal.general import handle_db_error
from app.dao.internal.historicos import registrar_log_generico_usuario
from app.dao.internal.usuarios import get_user
from app.decorators.decorators import admin_required
from app.extensions import db
from app.models.controle import EquipamentoDisponibilidade
from app.routes_helper.request import get_query_params, get_session_or_request
from config.database_views import get_url
from config.general import PER_PAGE

bp = Blueprint('database_equipamentos_disponibilidade', __name__, url_prefix="/database")

@bp.route('/equipamentos_disponibilidade', methods=['GET', 'POST'])
@admin_required
def gerenciar_equipamentos_disponibilidade():
    url = get_url('database_equipamentos_disponibilidade')
    redirect_action = None
    acao = get_session_or_request(request, session, 'acao', 'abertura')
    bloco = int(request.form.get('bloco', 0))
    page = int(request.form.get('page', 1))
    userid = session.get('userid')
    user = get_user(userid)
    extras: dict[str, Any] = {'url':url}
    if request.method == 'POST':
        if acao == "listar":
            sel_disponibilidade = select(EquipamentoDisponibilidade)
            disponibilidade_paginada = SelectPagination(
                select=sel_disponibilidade, session=db.session,
                page=page, per_page=PER_PAGE, error_out=False
            )
            extras['disponibilidades'] = disponibilidade_paginada.items
            extras['pagination'] = disponibilidade_paginada

        elif acao == "procurar" and bloco == 0:
            extras["equipamentos"] = get_equipamentos()
        elif acao == "procurar" and bloco == 1:
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
                filters.append(
                    or_(
                        EquipamentoDisponibilidade.data >= data_start
                    )
                )
            if data_end:
                filters.append(
                    or_(
                        EquipamentoDisponibilidade.data <= data_end
                    )
                )
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
                    page=page, per_page=PER_PAGE, error_out=False
                )
                extras['disponibilidades'] = disponibilidade_paginada.items
                extras['pagination'] = disponibilidade_paginada
                extras['query_params'] = query_params
            else:
                flash("especifique ao menos um campo", "danger")
                redirect_action, bloco = register_return(
                    url, acao, extras,
                    equipamentos = get_equipamentos()
                )

        elif acao == "inserir" and bloco == 0:
            extras["equipamentos"] = get_equipamentos()
        elif acao == "inserir" and bloco == 1:
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
                registrar_log_generico_usuario(userid, 'Inserção', novo_registro_disponibilidade)

                db.session.commit()
                flash("Disponibilidade criada com sucesso", "success")
            except DB_ERRORS as e:
                handle_db_error(e, "Erro ao criar disponibilidade")
            redirect_action, bloco = register_return(
                url, acao, extras, equipamentos=get_equipamentos()
            )
    if redirect_action:
        return redirect_action
    return render_template("database/table/equipamentos_disponibilidade.html", user=user, acao=acao, bloco=bloco, **extras)