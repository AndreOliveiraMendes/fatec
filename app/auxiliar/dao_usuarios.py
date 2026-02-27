from flask import current_app, session
from sqlalchemy import select

from app.extensions import db
from app.models.usuarios import Pessoas, Usuarios, Usuarios_Especiais

def get_pessoas(acao = None, userid = None):
    sel_pessoas = select(Pessoas.id_pessoa, Pessoas.nome_pessoa)
    if acao == 'excluir' and userid is not None:
        user = db.session.get(Usuarios, userid)
        if user:
            sel_pessoas = sel_pessoas.where(Pessoas.id_pessoa != user.id_usuario)
    sel_pessoas = sel_pessoas.order_by(Pessoas.nome_pessoa)
    return db.session.execute(sel_pessoas).all()

def get_pessoas_codigo():
    sel_pessoas = select(Pessoas.id_pessoa)
    return db.session.execute(sel_pessoas).scalars().all()

def get_usuarios(acao = None, userid = None):
    sel_usuarios = select(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas)
    if acao == 'excluir' and userid is not None:
        sel_usuarios = sel_usuarios.where(Usuarios.id_usuario != userid)
    return db.session.execute(sel_usuarios).all()

def get_user(userid):
    if not userid:
        return None

    user = db.session.get(Usuarios, userid)
    if user:
        return user

    current_app.logger.error(f"Usuário com ID {userid} não encontrado.")
    session.pop('userid')

def get_usuarios_especiais():
    sel_usuarios_especiais = select(Usuarios_Especiais)
    return db.session.execute(sel_usuarios_especiais).scalars().all()