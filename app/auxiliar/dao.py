from datetime import date

from flask import abort
from sqlalchemy import (and_, between, func, literal, or_, select, text,
                        union_all)
from sqlalchemy.exc import IntegrityError, MultipleResultsFound

from app.models import (Aulas, Aulas_Ativas, Dias_da_Semana,
                        DisponibilidadeEnum, Laboratorios, Pessoas,
                        Reservas_Fixas, Reservas_Temporarias, Semestres,
                        Situacoes_Das_Reserva, TipoAulaEnum,
                        TipoLaboratorioEnum, Turnos, Usuarios,
                        Usuarios_Especiais, db)
from config.general import FIRST_DAY_OF_WEEK, INDEX_START

#constantes auxiliares
Factor_Correcao = {"domingo":1, "segunda":0, "terça":6, "quarta":5, "quinta":4, "sexta":3, "sabado":2}

#funções espeficas para crude
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
def get_laboratorios(todos=True, sala=False):
    sel_laboratorios = select(Laboratorios)
    if not todos:
        filtro = []
        filtro.append(Laboratorios.disponibilidade == DisponibilidadeEnum.DISPONIVEL)
        if not sala:
            filtro.append(Laboratorios.tipo == TipoLaboratorioEnum.LABORATORIO)
        sel_laboratorios = sel_laboratorios.where(*filtro)
    return db.session.execute(sel_laboratorios).scalars().all()

#semestre
def get_semestres():
    sel_semestres = select(Semestres.id_semestre, Semestres.nome_semestre).order_by(Semestres.data_inicio)
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

#funcoes especificas para reservas
def get_aula_turno(turno:Turnos):
    return or_(
        between(Aulas.horario_inicio, turno.horario_inicio, turno.horario_fim),
        between(Aulas.horario_fim, turno.horario_inicio, turno.horario_fim)
    )

def get_aula_semana(dia:date):
    wd = dia.weekday()
    wd = (wd+Factor_Correcao[FIRST_DAY_OF_WEEK.lower()])%7
    if INDEX_START == 1:
        wd += 1
    return Aulas_Ativas.id_semana == wd

def get_aula_intervalo(inicio:date, fim:date):
    return or_(
        and_(
            Aulas_Ativas.inicio_ativacao.is_(None),
            Aulas_Ativas.fim_ativacao.is_(None)
        ), and_(
            Aulas_Ativas.inicio_ativacao.is_not(None),
            Aulas_Ativas.fim_ativacao.is_(None),
            Aulas_Ativas.inicio_ativacao <= fim
        ), and_(
            Aulas_Ativas.inicio_ativacao.is_(None),
            Aulas_Ativas.fim_ativacao.is_not(None),
            Aulas_Ativas.fim_ativacao >= inicio
        ), and_(
            Aulas_Ativas.inicio_ativacao.is_not(None),
            Aulas_Ativas.fim_ativacao.is_not(None),
            Aulas_Ativas.inicio_ativacao <= fim,
            Aulas_Ativas.fim_ativacao >= inicio
        )
    )

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

def get_aulas_extras(semestre:Semestres, turno:Turnos):
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
    filtro.append(get_aula_turno(turno))
    #pega somente as "aulas"
    filtro.append(Aulas_Ativas.tipo_aula == TipoAulaEnum.AULA.name)
    #executa o select
    sel_aulas_ativas = select(Aulas_Ativas, Aulas, Dias_da_Semana).select_from(Aulas_Ativas).join(Aulas).join(Dias_da_Semana).where(*filtro).order_by(Aulas_Ativas.id_semana, Aulas.horario_inicio)
    return db.session.execute(sel_aulas_ativas).all()

#condição unica da tabela reserva_temporaria
def check_reserva_temporaria(inicio, fim, laboratorio, aula, id = None):
    base_filter = [Reservas_Temporarias.id_reserva_laboratorio == laboratorio,
        Reservas_Temporarias.id_reserva_aula == aula]
    if id is not None:
        base_filter.append(Reservas_Temporarias.id_reserva_temporaria != id)
    base_filter.append(
        and_(Reservas_Temporarias.fim_reserva >= inicio, Reservas_Temporarias.inicio_reserva <= fim)
    )
    count_rtc = select(func.count()).select_from(Reservas_Temporarias).where(*base_filter)
    if db.session.scalar(count_rtc) > 0:
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("Já existe uma reserva para esse laboratorio e horario.")
        )

# get reservas_fixas por dia
def get_reservas_por_dia(dia:date, turno:Turnos|None=None, tipo_horario:TipoAulaEnum|None=None):
    sel_semestre = select(Semestres).where(
        between(dia, Semestres.data_inicio, Semestres.data_fim)
    )
    try:
        reservas_fixas, reservas_temporarias = None, None
        semestre = db.session.execute(sel_semestre).scalar_one_or_none()
        if semestre:
            filtro_fixa = [Reservas_Fixas.id_reserva_semestre == semestre.id_semestre]
            if turno is not None:
                filtro_fixa.append(get_aula_turno(turno))
            #dia da semana
            filtro_fixa.append(get_aula_semana(dia))
            #tipo horario
            if tipo_horario is not None:
                filtro_fixa.append(Aulas_Ativas.tipo_aula == tipo_horario)
            sel_reserva_fixa = (
                select(Reservas_Fixas).where(
                    *filtro_fixa
                ).select_from(Reservas_Fixas)
                .join(Aulas_Ativas)
                .join(Aulas)
                .join(Laboratorios)
                .order_by(
                    Aulas.horario_inicio,
                    Laboratorios.id_laboratorio
                )
            )
            reservas_fixas = db.session.execute(sel_reserva_fixa).scalars().all()
        filtro_temp = [between(dia, Reservas_Temporarias.inicio_reserva, Reservas_Temporarias.fim_reserva)]
        if turno is not None:
            filtro_temp.append(get_aula_turno(turno))
        #dia da semana
        filtro_temp.append(get_aula_semana(dia))
        #tipo horario
        if tipo_horario is not None:
            filtro_temp.append(Aulas_Ativas.tipo_aula == tipo_horario)
        sel_reserva_temporaria = (
            select(Reservas_Temporarias).where(
                *filtro_temp
            ).select_from(Reservas_Temporarias)
            .join(Aulas_Ativas)
            .join(Aulas)
            .join(Laboratorios)
            .order_by(
                Aulas.horario_inicio,
                Laboratorios.id_laboratorio
            )
        )
        reservas_temporarias = db.session.execute(sel_reserva_temporaria).scalars().all()
        return reservas_fixas, reservas_temporarias
    except MultipleResultsFound:
        abort(500)

# para gerenciar situacoes das reservas
def check_first(reserva_fixa:Reservas_Fixas, reserva_temporaria:Reservas_Temporarias):
    if reserva_fixa.aulas_ativas.aulas.horario_inicio < reserva_temporaria.aulas_ativas.aulas.horario_inicio:
        return 0
    elif reserva_fixa.aulas_ativas.aulas.horario_inicio > reserva_temporaria.aulas_ativas.aulas.horario_inicio:
        return 1
    else:
        if reserva_fixa.id_reserva_laboratorio < reserva_temporaria.id_reserva_laboratorio:
            return 0
        elif reserva_fixa.id_reserva_laboratorio > reserva_temporaria.id_reserva_laboratorio:
            return 1
        else:
            return 2

def get_situacoes_por_dia(aula:Aulas_Ativas, laboratorio:Laboratorios, dia:date):
    sel_situacoes = select(
        Situacoes_Das_Reserva
    ).where(
        Situacoes_Das_Reserva.id_situacao_aula == aula.id_aula_ativa,
        Situacoes_Das_Reserva.id_situacao_laboratorio == laboratorio.id_laboratorio,
        Situacoes_Das_Reserva.situacao_dia == dia
    )
    try:
        return db.session.execute(sel_situacoes).scalar_one_or_none()
    except MultipleResultsFound:
        abort(500)