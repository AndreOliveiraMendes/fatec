from flask import request
from datetime import datetime
from sqlalchemy.inspection import inspect
from models import db, Usuarios, Pessoas, Permissoes, Historicos

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

def registrar_log_generico(usuario_id, acao, instancia):
    """
    Registra um log para qualquer modelo do SQLAlchemy.
    
    - usuario_id: id do usuário que executou a ação
    - acao: 'Inserção', 'Edição', 'Exclusão', etc.
    - instancia: objeto de modelo (ex: nova_pessoa, novo_laboratorio...)
    """
    nome_tabela = instancia.__tablename__
    insp = inspect(instancia)

    # Tenta pegar a primary key dinamicamente
    chaves_primarias = [key.name for key in insp.mapper.primary_key]
    dados_chave = {chave: getattr(instancia, chave) for chave in chaves_primarias}

    # Tenta obter alguns campos relevantes
    campos_interessantes = ['nome', 'nome_pessoa', 'email', 'email_pessoa']
    dados_extras = {
        campo: getattr(instancia, campo, None)
        for campo in campos_interessantes
        if hasattr(instancia, campo)
    }

    descricao = f"[{acao}] Tabela: {nome_tabela.capitalize()} | Chave: {dados_chave}"
    if dados_extras:
        descricao += f" | Dados: {dados_extras}"

    log = Historicos()
    log.id_pessoa = Usuarios.query.get(usuario_id).id_pessoa
    log.acao = descricao
    log.dia = datetime.now()

    db.session.add(log)