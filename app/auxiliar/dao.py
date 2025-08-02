from datetime import date

from sqlalchemy import (and_, between, func, literal, or_, select, text,
                        union_all)
from sqlalchemy.exc import IntegrityError

from app.models import (Aulas, Aulas_Ativas, Dias_da_Semana,
                        DisponibilidadeEnum, Laboratorios, Pessoas,
                        Reservas_Fixas, Reservas_Temporarias, Semestres,
                        Situacoes_Das_Reserva, TipoAulaEnum,
                        TipoLaboratorioEnum, Turnos, Usuarios,
                        Usuarios_Especiais, db)


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
    sel_laboratorios = select(Laboratorios.id_laboratorio, Laboratorios.nome_laboratorio)
    if not todos:
        filtro = []
        filtro.append(Laboratorios.disponibilidade == DisponibilidadeEnum.DISPONIVEL)
        if not sala:
            filtro.append(Laboratorios.tipo == TipoLaboratorioEnum.LABORATORIO)
        sel_laboratorios.where(*filtro)
    return db.session.execute(sel_laboratorios).all()

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

def get_aulas_ativas_reservas_dia(dia: date, turno: Turnos|None=None, tipo_aula:TipoAulaEnum=TipoAulaEnum.AULA):
    filtros = []

    # Filtro de ativação no dia
    filtros.append(get_aula_intervalo(dia, dia))

    # Filtro de dia da semana
    filtros.append(Aulas_Ativas.id_semana == (dia.weekday()+1)%7+1)

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

def get_aulas_ativas_reservas_dias(dias_turnos: list[tuple[date, Turnos|None]], tipo_aula:TipoAulaEnum):
    selects = []

    for day, turno in dias_turnos:
        filtros = []

        # Filtro de ativação no dia
        filtros.append(get_aula_intervalo(day, day))

        # Filtro de dia da semana
        filtros.append(Aulas_Ativas.id_semana == (day.weekday()+1)%7+1)

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
                literal(day).label("dia_consulta"),
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
def get_aulas_ativas_reserva_semestre(semestre:Semestres, turno:Turnos|None=None, tipo_aula:TipoAulaEnum=TipoAulaEnum.AULA):
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