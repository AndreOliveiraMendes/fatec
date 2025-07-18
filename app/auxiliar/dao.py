from sqlalchemy import select
from app.models import db, Pessoas, Usuarios, Usuarios_Especiais, Aulas, Laboratorios, Semestres, \
    Dias_da_Semana, Turnos, Aulas_Ativas, Reservas_Fixas

#pessoas
def get_pessoas(acao = None, userid = None):
    sel_pessoas = select(Pessoas.id_pessoa, Pessoas.nome_pessoa)
    if userid:
        user = db.session.get(Usuarios, userid)
        if acao == 'excluir' and user:
            sel_pessoas = sel_pessoas.where(Pessoas.id_pessoa != user.id_usuario)
    return db.session.execute(sel_pessoas).all()

#usuarios
def get_usuarios(acao = None, userid = None):
    sel_usuarios = select(Usuarios.id_usuario, Pessoas.nome_pessoa).join(Pessoas)
    if acao == 'excluir' and userid is not None:
        sel_usuarios = sel_usuarios.where(Usuarios.id_usuario != userid)
    return db.session.execute(sel_usuarios).all()

#usuarios especiais
def get_usuarios_especiais():
    sel_usuarios_especiais = select(Usuarios_Especiais)
    return db.session.execute(sel_usuarios_especiais).scalars().all()

#aulas
def get_aulas():
    sel_aulas = select(Aulas)
    return db.session.execute(sel_aulas).scalars().all()

#laboratorios
def get_laboratorios():
    sel_laboratorios = select(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio)
    return db.session.execute(sel_laboratorios).all()

#semestre
def get_semestres():
    sel_semestres = select(Semestres.id_semestre, Semestres.nome_semestre)
    return db.session.execute(sel_semestres).all()

#dias da semana
def get_dias_da_semana():
    sel_dias_da_semanas = select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    return db.session.execute(sel_dias_da_semanas).scalars().all()

#turnos
def get_turnos():
    sel_turnos = select(Turnos.id_turno, Turnos.nome_turno).order_by(Turnos.id_turno)
    return db.session.execute(sel_turnos).all()

#Aulas Ativas
def get_aulas_ativas():
    sel_aulas_ativas = select(Aulas_Ativas)
    return db.session.execute(sel_aulas_ativas).scalars().all()

#Reservas Fixas
def get_reservas_fixas():
    sel_reservas_fixas = select(Reservas_Fixas)
    return db.session.execute(sel_reservas_fixas).scalars().all()