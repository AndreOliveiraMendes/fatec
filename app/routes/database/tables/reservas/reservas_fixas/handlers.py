from copy import copy

from flask import flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.dao_query import filtro_tipo_responsavel
from app.auxiliar.general import get_value_or_abort, none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.aulas import get_aulas_ativas, get_semestres
from app.dao.internal.locais import get_locais
from app.dao.internal.reservas import get_finalidade_reserva, get_reservas_fixas
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.reservas.reservas_laboratorios import Reservas_Fixas
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_reservas = select(Reservas_Fixas)
    reservas_fixas_paginada = SelectPagination(
        select=sel_reservas, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['reservas_fixas'] = reservas_fixas_paginada.items
    g.extras['pagination'] = reservas_fixas_paginada

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()
    g.extras['semestres'] = get_semestres()
    g.extras['finalidade_reservas'] = get_finalidade_reserva()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
    tipo_responsavel = none_if_empty(request.form.get('tipo_responsavel'), int)
    id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    id_reserva_semestre = none_if_empty(request.form.get('id_reserva_semestre'), int)
    id_finalidade_reserva = none_if_empty(request.form.get('id_finalidade_reserva'), int)
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))
    filters = []
    query_params = get_query_params(request)
    if id_reserva_fixa is not None:
        filters.append(Reservas_Fixas.id_reserva_fixa == id_reserva_fixa)
    if id_responsavel is not None:
        filters.append(Reservas_Fixas.id_responsavel == id_responsavel)
    if id_responsavel_especial is not None:
        filters.append(Reservas_Fixas.id_responsavel_especial == id_responsavel_especial)
    if tipo_responsavel is not None:
        filters.append(filtro_tipo_responsavel(Reservas_Fixas, tipo_responsavel))
    if id_reserva_local is not None:
        filters.append(Reservas_Fixas.id_reserva_local == id_reserva_local)
    if id_reserva_aula is not None:
        filters.append(Reservas_Fixas.id_reserva_aula == id_reserva_aula)
    if id_reserva_semestre is not None:
        filters.append(Reservas_Fixas.id_reserva_semestre == id_reserva_semestre)
    if id_finalidade_reserva is not None:
        filters.append(Reservas_Fixas.id_finalidade_reserva == id_finalidade_reserva)
    if observacoes:
        filters.append(Reservas_Fixas.observacoes.ilike(f"%{observacoes}%"))
    if descricao:
        filters.append(Reservas_Fixas.descricao.ilike(f"%{descricao}%"))
    if filters:
        sel_reservas = select(Reservas_Fixas).where(*filters)
        reservas_fixas_paginada = SelectPagination(
            select=sel_reservas, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['reservas_fixas'] = reservas_fixas_paginada.items
        g.extras['pagination'] = reservas_fixas_paginada
        g.extras['query_params'] = query_params
    else:
        flash("especifique ao menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(g.url,
            g.acao, g.extras,
            locais=get_locais(),
            aulas_ativas=get_aulas_ativas(),
            semestres=get_semestres(),
            finalidade_reservas=get_finalidade_reserva()
    )

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()
    g.extras['semestres'] = get_semestres()
    g.extras['finalidade_reservas'] = get_finalidade_reserva()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
    id_reserva_local = none_if_empty(request.form.get('id_reserva_local'), int)
    id_reserva_aula = none_if_empty(request.form.get('id_reserva_aula'), int)
    id_reserva_semestre = none_if_empty(request.form.get('id_reserva_semestre'), int)
    id_finalidade_reserva = none_if_empty(request.form.get('id_finalidade_reserva'), int)
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))

    nova_reserva_fixa = Reservas_Fixas(
        id_responsavel=id_responsavel,
        id_responsavel_especial=id_responsavel_especial,
        id_reserva_local=id_reserva_local,
        id_reserva_aula=id_reserva_aula,
        id_reserva_semestre=id_reserva_semestre,
        id_finalidade_reserva=id_finalidade_reserva,
        observacoes=observacoes,
        descricao=descricao
    )

    db_action(
        "Inserção",
        "Reserva semanal cadastrada com sucesso",
        "Erro ao cadastrar reserva",
        obj=nova_reserva_fixa
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        locais=get_locais(),
        aulas_ativas=get_aulas_ativas(),
        semestres=get_semestres(),
        finalidade_reservas=get_finalidade_reserva()
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_reservas_fixas():
    g.extras['reservas_fixas'] = get_reservas_fixas()

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_reserva_fixa():
    id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)
    reserva_fixa = db.get_or_404(Reservas_Fixas, id_reserva_fixa)
    g.extras['reserva_fixa'] = reserva_fixa
    g.extras['locais'] = get_locais()
    g.extras['aulas_ativas'] = get_aulas_ativas()
    g.extras['semestres'] = get_semestres()
    g.extras['finalidade_reservas'] = get_finalidade_reserva()

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)
    id_responsavel = none_if_empty(request.form.get('id_responsavel'), int)
    id_responsavel_especial = none_if_empty(request.form.get('id_responsavel_especial'), int)
    id_reserva_local = get_value_or_abort(request.form.get('id_reserva_local'), 400, "id do local é obrigatorio", int)
    id_reserva_aula = get_value_or_abort(request.form.get('id_reserva_aula'), 400, "id da aula é obrigatorio", int)
    id_reserva_semestre = get_value_or_abort(request.form.get('id_reserva_semestre'), 400, "id do semestre é obrigatorio", int)
    id_finalidade_reserva = none_if_empty(request.form.get('id_finalidade_reserva'), int)
    observacoes = none_if_empty(request.form.get('observacoes'))
    descricao = none_if_empty(request.form.get('descricao'))

    reserva_fixa = db.get_or_404(Reservas_Fixas, id_reserva_fixa)
    dados_anteriores = copy(reserva_fixa)

    def update():
        reserva_fixa.id_responsavel = id_responsavel
        reserva_fixa.id_responsavel_especial = id_responsavel_especial
        reserva_fixa.id_reserva_local = id_reserva_local
        reserva_fixa.id_reserva_aula = id_reserva_aula
        reserva_fixa.id_reserva_semestre = id_reserva_semestre
        reserva_fixa.id_finalidade_reserva = id_finalidade_reserva
        reserva_fixa.observacoes = observacoes
        reserva_fixa.descricao = descricao

    db_action(
        "Edição",
        "Reserva editada com sucesso",
        "Erro ao editar reserva",
        obj=reserva_fixa,
        old_obj=dados_anteriores,
        action=update
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        reservas_fixas=get_reservas_fixas()
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_reserva_fixa = none_if_empty(request.form.get('id_reserva_fixa'), int)

    reserva_fixa = db.get_or_404(Reservas_Fixas, id_reserva_fixa)

    db_action(
        "Exclusão",
        "Reserva excluida com sucesso",
        "Erro ao excluir reserva",
        obj=reserva_fixa
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        reservas_fixas=get_reservas_fixas()
    )