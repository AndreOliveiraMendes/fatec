import copy
import operator
from functools import reduce

from flask import Request, flash, g, request
from flask_sqlalchemy.pagination import SelectPagination
from sqlalchemy import select

from app.auxiliar.constant import Permission
from app.auxiliar.general import none_if_empty
from app.auxiliar.navigation import register_return
from app.dao.internal.usuarios import get_usuarios
from app.decorators.decorators import register_handler
from app.extensions import db
from app.models.usuarios import Permissoes, Pessoas, Usuarios
from app.routes_helper.db_actions import db_action
from app.routes_helper.request import get_query_params
from config.general import PER_PAGE

dispatcher = {}

def get_no_perm_users():
    sel_users_permission = select(Permissoes.id_permissao_usuario)
    sel_permissionless = select(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas).filter(
        ~Usuarios.id_usuario.in_(sel_users_permission)
    )
    return db.session.execute(sel_permissionless).all()

def get_perm(acao, userid):
    sel_permissoes = select(
        Permissoes.id_permissao_usuario, Pessoas.nome_pessoa
    ).select_from(Permissoes).join(Usuarios).join(Pessoas)
    if acao == 'excluir':
        sel_permissoes = sel_permissoes.where(Permissoes.id_permissao_usuario!=userid)
    return db.session.execute(sel_permissoes).all()

def get_flag(req: Request) -> int:
    flags = {
        "flag_fixa": Permission.RESERVA_FIXA,
        "flag_temp": Permission.RESERVA_TEMPORARIA,
        "flag_auditorio": Permission.RESERVA_AUDITORIO,
        "flag_admin": Permission.ADMIN,
        "flag_autorizar": Permission.AUTORIZAR,
        "flag_cmd_config": Permission.CMD_CONFIG,
    }
    return reduce(operator.or_, (v for k, v in flags.items() if k in req.form), 0)

@register_handler(dispatcher, 'listar', 0)
def list_handler():
    sel_permissoes = select(Permissoes)
    permissoes_paginadas = SelectPagination(
        select=sel_permissoes, session=db.session,
        page=g.page, per_page=PER_PAGE, error_out=False
    )
    g.extras['permissoes'] = permissoes_paginadas.items
    g.extras['pagination'] = permissoes_paginadas
    g.extras['userid'] = g.userid

@register_handler(dispatcher, 'procurar', 0)
def search_prefetch():
    g.extras['users'] = get_usuarios()

@register_handler(dispatcher, 'procurar', 1)
def search_fetch():
    id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
    flag = get_flag(request)
    modobusca = none_if_empty(request.form.get('modobusca')) 
    filters = []
    query_params = get_query_params(request)
    if id_permissao_usuario is not None:
        filters.append(Permissoes.id_permissao_usuario==id_permissao_usuario)
    if flag > 0:
        if modobusca == 'ou':
            filters.append(Permissoes.permissao.bitwise_and(flag) > 0)
        else:
            filters.append(Permissoes.permissao.bitwise_and(flag) == flag)
    if filters:
        sel_permissoes = select(Permissoes).where(*filters)
        permissoes_paginadas = SelectPagination(
            select=sel_permissoes, session=db.session,
            page=g.page, per_page=PER_PAGE, error_out=False
        )
        g.extras['permissoes'] = permissoes_paginadas.items
        g.extras['pagination'] = permissoes_paginadas
        g.extras['userid'] = g.userid
        g.extras['query_params'] = query_params
    else:
        flash("especifique pelo menos um campo", "danger")
        g.redirect_action, g.bloco = register_return(
            g.url, g.acao, g.extras, users=get_usuarios()
        )

@register_handler(dispatcher, 'inserir', 0)
def insert_prefetch():
    g.extras['users'] = get_no_perm_users()

@register_handler(dispatcher, 'inserir', 1)
def insert_push():
    id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
    flag = get_flag(request)

    nova_permissao = Permissoes(
        id_permissao_usuario=id_permissao_usuario,
        permissao=flag
    )

    def insert():
        db.session.add(nova_permissao)

    db_action(
        "Inserção",
        "Permissao cadastrada com sucesso",
        "Erro ao cadastrar permissão",
        obj=nova_permissao,
        action=insert,
        observacao=f"0b{flag:03b}"
    )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        users=get_no_perm_users()
    )

@register_handler(dispatcher, 'editar', 0)
@register_handler(dispatcher, 'excluir', 0)
def fetch_permissoes():
    g.extras['permissoes'] = get_perm(g.acao, g.userid)

@register_handler(dispatcher, 'editar', 1)
@register_handler(dispatcher, 'excluir', 1)
def fetch_permissao():
    usuario = none_if_empty(request.form.get('id_usuario'))
    permissao = db.get_or_404(Permissoes, usuario)
    g.extras['permissao'] = permissao
    g.extras['userid'] = g.userid

@register_handler(dispatcher, 'editar', 2)
def edit_push():
    id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)
    flag = get_flag(request)

    permissao = db.get_or_404(Permissoes, id_permissao_usuario)

    if id_permissao_usuario == g.userid and flag & Permission.ADMIN == 0:
        flash("voce não pode remover seu proprio poder de administrador", "danger")

    else:
        dados_anteriores = copy.copy(permissao)

        def update():
            permissao.permissao = flag

        observacao = f"0b{dados_anteriores.permissao:03b} → 0b{flag:03b}"

        db_action(
            "Edição",
            "Permissao atualizada com sucesso",
            "Erro ao editar permissão",
            obj=permissao,
            old_obj=dados_anteriores,
            action=update,
            observacao=observacao
        )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        permissoes=get_perm(g.acao, g.userid)
    )

@register_handler(dispatcher, 'excluir', 2)
def delete_push():
    id_permissao_usuario = none_if_empty(request.form.get('id_permissao_usuario'), int)

    permissao = db.get_or_404(Permissoes, id_permissao_usuario)

    if id_permissao_usuario == g.userid:
        flash("voce não pode remover sua propria permissão", "danger")

    else:

        def delete():
            db.session.delete(permissao)

        db_action(
            "Exclusão",
            "Permissao excluída com sucesso",
            "Erro ao excluir permissão",
            obj=permissao,
            action=delete,
            observacao=f"0b{permissao.permissao:03b}"
        )

    g.redirect_action, g.bloco = register_return(
        g.url, g.acao, g.extras,
        permissoes=get_perm(g.acao, g.userid)
    )