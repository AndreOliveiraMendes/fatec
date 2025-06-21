from flask import request
from models import Usuarios, Pessoas, Usuarios_Permissao

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']

def none_if_empty(value):
    return value if value and value.strip() else None

def get_query_params(request):
    return {key: value for key, value in request.form.items() if key not in IGNORED_FORM_FIELDS}

def get_user_info(userid):
    username, perm = None, 0
    if not userid:
        return username, perm
    user = Usuarios.query.filter_by(id_usuario=userid).first()
    if user:
        pessoa = Pessoas.query.filter_by(id_pessoa=user.id_pessoa).first()
        username = pessoa.nome_pessoa
        permissao = Usuarios_Permissao.query.filter_by(id_permissao_usuario=user.id_usuario).first()
        if permissao:
            perm = permissao.permissao
    return username, perm