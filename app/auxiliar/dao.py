from sqlalchemy import select
from app.models import db, Pessoas, Usuarios, Usuarios_Especiais, Aulas, Laboratorios, Semestres, \
    Dias_da_Semana, Turnos, Aulas_Ativas

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

#usuarios especiais
def get_usuarios_especiais():
    sue = select(Usuarios_Especiais)
    return db.session.execute(sue).scalars().all()

#aulas
def get_aulas():
    sa = select(Aulas)
    return db.session.execute(sa).scalars().all()

#laboratorios
def get_laboratorios():
    slin = select(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio)
    return db.session.execute(slin).all()

#semestre
def get_semestre():
    ssin = select(Semestres.id_semestre, Semestres.nome_semestre)
    return db.session.execute(ssin).all()

#dias da semana
def get_dias_da_semana():
    sds = select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    return db.session.execute(sds).scalars().all()

#turnos
def get_turnos():
    stin = select(Turnos.id_turno, Turnos.nome_turno).order_by(Turnos.id_turno)
    return db.session.execute(stin).all()

#Aulas Ativas
def get_aulas_ativas():
    saa = select(Aulas_Ativas)
    return db.session.execute(saa).scalars().all()