from datetime import date, time

from flask import abort
from sqlalchemy import and_, func, literal, or_, select, text, union_all
from sqlalchemy.exc import IntegrityError, MultipleResultsFound

from app.auxiliar.auxiliar_dao import (get_aula_intervalo, get_aula_semana,
                                       get_aula_turno)
from app.extensions import db
from app.model.aulas import (Aulas, Aulas_Ativas, Dias_da_Semana, Semestres,
                              TipoAulaEnum, Turnos)


def get_aulas():
    sel_aulas = select(Aulas)
    return db.session.execute(sel_aulas).scalars().all()

def get_aulas_ativas():
    sel_aulas_ativas = select(Aulas_Ativas)
    return db.session.execute(sel_aulas_ativas).scalars().all()

def get_semestres():
    sel_semestres = select(Semestres.id_semestre, Semestres.nome_semestre).order_by(Semestres.data_inicio)
    return db.session.execute(sel_semestres).all()

def get_aulas_ativas_por_dia(dia: date, turno: Turnos|None=None, tipo_aula:TipoAulaEnum=TipoAulaEnum.AULA):
    filtros = []

    # Filtro de ativação no dia
    filtros.append(get_aula_intervalo(dia, dia))

    # Filtro de dia da semana
    filtros.append(get_aula_semana(dia))

    # Filtro de turno
    if turno is not None:
        filtros.append(get_aula_turno(turno))

    # Filtro de tipo de horario
    filtros.append(Aulas_Ativas.tipo_aula == tipo_aula)

    sel_aulas_ativas = (
        select(Aulas_Ativas, Aulas, Dias_da_Semana)
        .select_from(Aulas_Ativas)
        .join(Aulas)
        .join(Dias_da_Semana)
        .where(*filtros)
        .order_by(Aulas.horario_inicio)
    )
    return db.session.execute(sel_aulas_ativas).all()

def get_aulas_ativas_por_lista_de_dias(dias_turnos: list[tuple[date, Turnos|None]], tipo_aula:TipoAulaEnum):
    selects = []

    for dia, turno in dias_turnos:
        filtros = []

        # Filtro de ativação no dia
        filtros.append(get_aula_intervalo(dia, dia))

        # Filtro de dia da semana
        filtros.append(get_aula_semana(dia))

        # Filtro de turno
        if turno is not None:
            filtros.append(get_aula_turno(turno))

        # Filtro de tipo de horario
        filtros.append(Aulas_Ativas.tipo_aula == tipo_aula)

        #nome turno
        nome_turno = turno.nome_turno if turno else ""

        # SELECT individual com labels (pra saber de que dia/turno veio)
        sel = (
            select(
                Aulas_Ativas,
                Aulas,
                Dias_da_Semana,
                literal(dia).label("dia_consulta"),
                literal(nome_turno).label("turno_consulta")
            )
            .select_from(Aulas_Ativas)
            .join(Aulas)
            .join(Dias_da_Semana)
            .where(*filtros)
        )

        selects.append(sel)

    # Junta todos os selects com UNION ALL
    consulta_final = union_all(*selects).order_by(text("dia_consulta"), "horario_inicio")

    return db.session.execute(consulta_final).all()

#aulas ativas para um determinado semestre
def get_aulas_ativas_por_semestre(semestre:Semestres, turno:Turnos|None=None, tipo_aula:TipoAulaEnum=TipoAulaEnum.AULA):
    filtros = []
    #verifica quais horarios estão disponiveis naquele semestre
    filtros.append(get_aula_intervalo(semestre.data_inicio, semestre.data_fim))
    #verifica quais horarios estão naquele turno
    if turno is not None:
        filtros.append(get_aula_turno(turno))
    #verifica se o horario é destinado a aula
    filtros.append(Aulas_Ativas.tipo_aula == tipo_aula)
    #efetua o query e executa ele
    sel_aulas_ativas = select(Aulas_Ativas, Aulas, Dias_da_Semana).select_from(Aulas_Ativas).join(Aulas).join(Dias_da_Semana).where(*filtros).order_by(Aulas_Ativas.id_semana, Aulas.horario_inicio)
    return db.session.execute(sel_aulas_ativas).all()

def get_aulas_extras(semestre:Semestres, turno:Turnos|None):
    filtro = []
    #aulas que não ocupam todo semestre
    filtro.append(
        or_(
            and_(
                Aulas_Ativas.inicio_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao.is_(None),
                Aulas_Ativas.inicio_ativacao <= semestre.data_fim,
                Aulas_Ativas.inicio_ativacao > semestre.data_inicio
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_(None),
                Aulas_Ativas.fim_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao >= semestre.data_inicio,
                Aulas_Ativas.fim_ativacao < semestre.data_fim
            ), and_(
                Aulas_Ativas.inicio_ativacao.is_not(None),
                Aulas_Ativas.fim_ativacao.is_not(None),
                Aulas_Ativas.inicio_ativacao <= semestre.data_fim,
                Aulas_Ativas.fim_ativacao >= semestre.data_inicio,
                or_(
                    Aulas_Ativas.inicio_ativacao > semestre.data_inicio,
                    Aulas_Ativas.fim_ativacao < semestre.data_fim
                )
            )
        )
    )

    #logica usual do turno
    if turno:
        filtro.append(get_aula_turno(turno))
    #pega somente as "aulas"
    filtro.append(Aulas_Ativas.tipo_aula == TipoAulaEnum.AULA.name)
    #executa o select
    sel_aulas_ativas = select(Aulas_Ativas, Aulas, Dias_da_Semana).select_from(Aulas_Ativas).join(Aulas).join(Dias_da_Semana).where(*filtro).order_by(Aulas_Ativas.id_semana, Aulas.horario_inicio)
    return db.session.execute(sel_aulas_ativas).all()

def get_turno_by_time(hora:time):
    try:
        hora_truncada = hora.replace(second=0, microsecond=0)
        return db.session.execute(
            select(Turnos).where(
                Turnos.horario_inicio <= hora_truncada,
                hora_truncada <= Turnos.horario_fim
            )
        ).scalar_one_or_none()
    except MultipleResultsFound as e:
        return None
    
def get_dias_da_semana():
    sel_dias_da_semana = select(Dias_da_Semana).order_by(Dias_da_Semana.id_semana)
    return db.session.execute(sel_dias_da_semana).scalars().all()

def get_turnos():
    sel_turnos = select(Turnos.id_turno, Turnos.nome_turno).order_by(Turnos.id_turno)
    return db.session.execute(sel_turnos).all()

def check_aula_ativa(inicio, fim, aula, semana, tipo, id = None):
    base_filter = [Aulas_Ativas.id_aula == aula, Aulas_Ativas.id_semana == semana,
                   Aulas_Ativas.tipo_aula == tipo]
    if id is not None:
        base_filter.append(Aulas_Ativas.id_aula_ativa != id)
    if inicio and fim:
        base_filter.append(
            and_(
                or_(Aulas_Ativas.fim_ativacao.is_(None), Aulas_Ativas.fim_ativacao >= inicio),
                or_(Aulas_Ativas.inicio_ativacao.is_(None), Aulas_Ativas.inicio_ativacao <= fim)
                )
            )
    elif inicio and not fim:
        base_filter.append(
            or_(Aulas_Ativas.fim_ativacao.is_(None), Aulas_Ativas.fim_ativacao >= inicio)
            )
    elif not inicio and fim:
        base_filter.append(
            or_(Aulas_Ativas.inicio_ativacao.is_(None), Aulas_Ativas.inicio_ativacao <= fim)
            )
    countl_sel_aulas_ativas = select(func.count()).select_from(Aulas_Ativas).where(*base_filter)
    res = db.session.scalar(countl_sel_aulas_ativas)
    if res is None:
        abort(500, description="Erro ao verificar conflito de aula ativa.")
    if res > 0:
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("Já existe uma aula ativa com os mesmos dados (aula, semana e tipo).")
        )