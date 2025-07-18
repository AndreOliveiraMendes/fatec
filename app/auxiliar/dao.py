from sqlalchemy import select
from app.models import db, Pessoas, Usuarios, Usuarios_Especiais, Aulas, Laboratorios

#pessoas
def get_pessoas(acao = None, userid = None):
    spin = select(Pessoas.id_pessoa, Pessoas.nome_pessoa)
    if userid:
        user = db.session.get(Usuarios, userid)
        if acao == 'excluir' and user:
            spin = spin.where(Pessoas.id_pessoa != user.id_usuario)
    return db.session.execute(spin).scalars().all()

#usuarios
def get_usuarios(acao = None, userid = None):
    suin = select(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas)
    if acao == 'excluir' and userid is not None:
        suin = suin.where(Usuarios.id_usuario != userid)
    return db.session.execute(suin).scalars().all()

#usuarios especiais
def get_usuarios_especiais():
    suein = select(Usuarios_Especiais)
    return db.session.execute(suein).scalars().all()

#aulas
def get_aulas():
    sa = select(Aulas)
    return db.session.execute(sa).scalars().all()

#laboratorios
def get_laboratorios():
    slin = select(Laboratorios)
    return db.session.execute(slin).scalars().all()