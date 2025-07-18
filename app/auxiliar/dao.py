from sqlalchemy import select
from app.models import db, Pessoas, Usuarios

#pessoas
def get_pessoas(acao = None, userid = None):
    spin = select(Pessoas.id_pessoa, Pessoas.nome_pessoa)
    if userid:
        user = db.session.get(Usuarios, userid)
        if acao == 'excluir' and user:
            spin = spin.where(Pessoas.id_pessoa != user.id_usuario)
    return db.session.execute(spin).all()

#usuarios
def get_usuarios(acao = None, userid = None):
    suin = select(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas)
    if acao == 'excluir' and userid is not None:
        suin = suin.where(Usuarios.id_usuario != userid)
    return db.session.execute(suin).all()