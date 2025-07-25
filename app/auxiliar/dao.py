from sqlalchemy import select, and_, or_, between
from datetime import date
from app.models import db, Pessoas, Usuarios, Usuarios_Especiais, Aulas, Laboratorios, Semestres, \
    Dias_da_Semana, Turnos, Aulas_Ativas, Reservas_Fixas, Reservas_Temporarias, Situacoes_Das_Reserva, \
    DisponibilidadeEnum

#pessoas
def get_pessoas(acao = None, userid = None):
    sel_pessoas = select(Pessoas.id_pessoa, Pessoas.nome_pessoa)
    if acao == 'excluir' and userid is not None:
        user = db.session.get(Usuarios, userid)
        if user:
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
def get_laboratorios(todos=True):
    sel_laboratorios = select(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio)
    if not todos:
        sel_laboratorios.where(Laboratorios.disponibilidade == DisponibilidadeEnum.DISPONIVEL)
    return db.session.execute(sel_laboratorios).all()

#semestre
def get_semestres():
    sel_semestres = select(Semestres.id_semestre, Semestres.nome_semestre)
    return db.session.execute(sel_semestres).all()

#dias da semana
def get_dias_da_semana():
    sel_dias_da_semana = select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    return db.session.execute(sel_dias_da_semana).scalars().all()

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

#Reservas Temporarias
def get_reservas_temporarias():
    sel_reservas_temporarias = select(Reservas_Temporarias)
    return db.session.execute(sel_reservas_temporarias).scalars().all()

#Situacoes das Reservas
def get_situacoes():
    sel_situacoes_das_reservas = select(Situacoes_Das_Reserva)
    return db.session.execute(sel_situacoes_das_reservas).scalars().all()

#aulas ativas para as reservas
def get_aulas_ativas_reserva(day:date, turno:Turnos):
    filtro = []
    #verifica quais horarios estão disponiveis hoje
    filtro.append(
        or_(
            and_(
                Aulas_Ativas.inicio_ativacao.is_(None),
                Aulas_Ativas.fim_ativacao.is_(None)
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao.is_(None),
                Aulas_Ativas.inicio_ativacao <= day
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_(None),
                Aulas_Ativas.fim_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao >= day
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao.is_not(None),
                between(day, Aulas_Ativas.inicio_ativacao, Aulas_Ativas.fim_ativacao)
            )
        )
    )
    #verifica quais horarios estão naquele turno
    filtro.append(
        or_(
            between(Aulas.horario_inicio, turno.horario_inicio, turno.horario_fim),
            between(Aulas.horario_fim, turno.horario_inicio, turno.horario_fim)
        )
    )
    sel_aulas_ativas = select(Aulas_Ativas, Aulas, Dias_da_Semana).select_from(Aulas_Ativas).join(Aulas).join(Dias_da_Semana).where(*filtro).order_by(Aulas_Ativas.id_semana, Aulas.horario_inicio)
    return db.session.execute(sel_aulas_ativas).all()