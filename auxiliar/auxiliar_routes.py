from flask import request
from models import Usuarios, Pessoas, Permissoes

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

def none_if_empty(value):
    return value if value and value.strip() else None

def get_query_params(request):
    return {key: value for key, value in request.form.items() if key not in IGNORED_FORM_FIELDS}

def get_user_info(userid):
    username, perm = None, 0
    if not userid:
        return username, perm
    user = Usuarios.query.get(userid)
    if user:
        pessoa = Pessoas.query.get(user.id_usuario)
        username = pessoa.nome_pessoa
        permissao = Permissoes.query.get(userid)
        if permissao:
            perm = permissao.permissao
    return username, perm