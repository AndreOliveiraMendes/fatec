from datetime import date, datetime, time

from sqlalchemy import (TEXT, CheckConstraint, Enum, ForeignKey, String,
                        UniqueConstraint, case)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import Base, db
from app.enums import (DisponibilidadeEnum, FinalidadeReservaEnum, OrigemEnum,
                       SituacaoChaveEnum, StatusReservaAuditorioEnum,
                       TipoAulaEnum, TipoLocalEnum, TipoReservaEnum)


def parse_time(time):
    return time.strftime('%H:%M') if time else None

def parse_date(date):
    return date.strftime('%d/%m/%Y') if date else None

class Exibicao_Reservas(Base):
    __tablename__ = "exibicao_reservas"
    id_exibicao:Mapped[int] = mapped_column(primary_key=True)
    id_exibicao_local:Mapped[int] = mapped_column(ForeignKey("locais.id_local"), nullable=False)
    id_exibicao_aula:Mapped[int] = mapped_column(ForeignKey("aulas_ativas.id_aula_ativa"), nullable=False)
    exibicao_dia:Mapped[date] = mapped_column(nullable=False)

    tipo_reserva: Mapped[TipoReservaEnum] = mapped_column(
        Enum(TipoReservaEnum, name="tipo_reserva_enum", create_constraint=True),
        server_default=TipoReservaEnum.TEMPORARIA.name
    )

    __table_args__ = (
        UniqueConstraint(
            'id_exibicao_local',
            'id_exibicao_aula',
            'exibicao_dia',
            name="uq_exibicao_local_aula_dia"
        ),
    )

    local: Mapped['Locais'] = relationship(back_populates='exibicao_reservas')
    aula_ativa: Mapped['Aulas_Ativas'] = relationship(back_populates='exibicao_reservas')

    @property
    def selector_identification(self):
        aula = self.aula_ativa.selector_identification
        local = self.local.nome_local
        dia = parse_date(self.exibicao_dia)
        return f" {dia} no {local} as {aula}"

    def __repr__(self):
        return (
            f"Exibicao_Reservas(id_exibicao={self.id_exibicao}, id_exibicao_local={self.id_exibicao_local}, "
            f"id_exibicao_aula={self.id_exibicao_aula}, exibicao_dia={self.exibicao_dia}, "
            f"tipo_reserva={self.tipo_reserva})"
        )

class Situacoes_Das_Reserva(Base):
    __tablename__ = "situacoes_das_reservas"

    id_situacao:Mapped[int] = mapped_column(primary_key=True)
    id_situacao_local:Mapped[int] = mapped_column(ForeignKey("locais.id_local"), nullable=False)
    id_situacao_aula:Mapped[int] = mapped_column(ForeignKey("aulas_ativas.id_aula_ativa"), nullable=False)
    situacao_dia:Mapped[date] = mapped_column(nullable=False)

    situacao_chave: Mapped[SituacaoChaveEnum] = mapped_column(
        Enum(SituacaoChaveEnum, name="situacao_chave_enum", create_constraint=True),
        server_default=SituacaoChaveEnum.NAO_PEGOU_A_CHAVE.name
    )

    tipo_reserva: Mapped[TipoReservaEnum] = mapped_column(
        Enum(TipoReservaEnum, name="tipo_reserva_enum", create_constraint=True),
        server_default=TipoReservaEnum.FIXA.name
    )

    __table_args__ = (
        UniqueConstraint(
            'id_situacao_local',
            'id_situacao_aula',
            'situacao_dia',
            'tipo_reserva',
            name="uq_situacao_local_aula_dia_tipo"
        ),
    )

    local: Mapped['Locais'] = relationship(back_populates='situacoes_das_reservas')
    aula_ativa: Mapped['Aulas_Ativas'] = relationship(back_populates='situacoes_das_reservas')

    @property
    def selector_identification(self):
        aula = self.aula_ativa.selector_identification
        local = self.local.nome_local
        dia = parse_date(self.situacao_dia)
        return f" {dia} no {local} as {aula}"

    def __repr__(self) -> str:
        return (
            f"<SituacaoReserva(id_situacao={self.id_situacao}, id_situacao_local={self.id_situacao_local}, "
            f"id_situacao_aula={self.id_situacao_aula}, situacao_dia={self.situacao_dia} "
            f"situacao_chave={self.situacao_chave.value})>"
        )

class Reservas_Auditorios(Base):
    __tablename__ = "reservas_auditorios"
    
    id_reserva_auditorio: Mapped[int] = mapped_column(primary_key=True)
    id_responsavel: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    id_reserva_local: Mapped[int] = mapped_column(ForeignKey('locais.id_local'), nullable=False)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    
    dia_reserva: Mapped[date] = mapped_column(nullable=False)
    status_reserva: Mapped[StatusReservaAuditorioEnum] = mapped_column(
        Enum(StatusReservaAuditorioEnum, name="status_reserva_enum", create_constraint=True),
        server_default=StatusReservaAuditorioEnum.AGUARDANDO.name
    )
    
    id_autorizador: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    observação_responsavel: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    observação_autorizador: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            'id_responsavel',
            'id_reserva_local',
            'id_reserva_aula',
            'dia_reserva',
            name='uq_reserva_responsavel_local_aula_dia'
        ),
    )

    local: Mapped['Locais'] = relationship("Locais", back_populates="reservas_auditorios")
    aula_ativa: Mapped['Aulas_Ativas'] = relationship("Aulas_Ativas", back_populates="reservas_auditorios")
    responsavel: Mapped['Pessoas'] = relationship("Pessoas", back_populates="reservas_responsavel", foreign_keys=[id_responsavel])
    autorizador: Mapped['Pessoas'] = relationship("Pessoas", back_populates="reservas_autorizador", foreign_keys=[id_autorizador])

    @property
    def selector_identification(self):
        local = self.local.nome_local
        aula = self.aula_ativa.selector_identification
        dia = self.dia_reserva
        return f" {aula} em {local} no dia {dia}"

    def __repr__(self):
        return (
            f"ReservaAuditorio(id_reserva_auditorio={self.id_reserva_auditorio}, "
            f"id_responsavel={self.id_responsavel}, "
            f"id_reserva_local={self.id_reserva_local}, "
            f"id_reserva_aula={self.id_reserva_aula}, "
            f"dia_reserva={self.dia_reserva}, "
            f"status_reserva={self.status_reserva}, "
            f"id_autorizador={self.id_autorizador}, "
            f"observação_responsavel={self.observação_responsavel}, "
            f"observação_autorizador={self.observação_autorizador})"
        )

class ReservaBase(Base):  # herda de Base
    __abstract__ = True   # não vira tabela
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    id_responsavel_especial: Mapped[int | None] = mapped_column(ForeignKey('usuarios_especiais.id_usuario_especial'), nullable=True)
    id_reserva_local: Mapped[int] = mapped_column(ForeignKey('locais.id_local'), nullable=False)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    finalidade_reserva: Mapped[FinalidadeReservaEnum] = mapped_column(
        Enum(FinalidadeReservaEnum, name="tipo_reserva_enum", create_constraint=True),
        server_default=FinalidadeReservaEnum.GRADUACAO.name
    )
    observacoes: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    descricao: Mapped[str | None] = mapped_column(String(100), nullable=True)

    @hybrid_property
    def tipo_responsavel(self):
        if self.id_responsavel is not None and self.id_responsavel_especial is None:
            return 0
        elif self.id_responsavel_especial is None and self.id_responsavel is not None:
            return 1
        elif self.id_responsavel is not None and self.id_responsavel_especial is not None:
            return 2
        else:
            return 3

    @tipo_responsavel.expression
    def tipo_responsavel(cls):
        return case(
            (cls.id_responsavel.isnot(None) & cls.id_responsavel_especial.is_(None), 0),
            (cls.id_responsavel.is_(None) & cls.id_responsavel_especial.isnot(None), 1),
            (cls.id_responsavel.isnot(None) & cls.id_responsavel_especial.isnot(None), 2),
            else_=3  # Valor padrão se nenhuma condição for atendida
        )

class Reservas_Fixas(ReservaBase):
    __tablename__ = 'reservas_fixas'

    id_reserva_fixa: Mapped[int] = mapped_column(primary_key=True)
    id_reserva_semestre: Mapped[int] = mapped_column(ForeignKey('semestres.id_semestre'), nullable=False)

    semestre: Mapped['Semestres'] = relationship(back_populates='reservas_fixas')

    __table_args__ = (
        UniqueConstraint(
            'id_reserva_local',
            'id_reserva_aula',
            'id_reserva_semestre',
            name='uq_reserva_local_aula_semestre'
        ),
    )

    pessoa: Mapped['Pessoas'] = relationship("Pessoas", back_populates="reservas_fixas")
    usuario_especial: Mapped['Usuarios_Especiais'] = relationship("Usuarios_Especiais", back_populates="reservas_fixas")
    local: Mapped['Locais'] = relationship("Locais", back_populates="reservas_fixas")
    aula_ativa: Mapped['Aulas_Ativas'] = relationship("Aulas_Ativas", back_populates="reservas_fixas")

    @property
    def selector_identification(self):
        local = self.local.nome_local
        aula = self.aula_ativa.selector_identification
        semestre = self.semestre.nome_semestre
        return f" {aula} em {local} no {semestre}"
    
    def __repr__(self):
        return (
            f"Reservas_Fixas(id_reserva_fixa={self.id_reserva_fixa}, id_responsavel={self.id_responsavel}, "
            f"id_responsavel_especial={self.id_responsavel_especial}, tipo_responsavel={self.tipo_responsavel}, "
            f"id_reserva_local={self.id_reserva_local}, id_reserva_aula={self.id_reserva_aula}, "
            f"finalidade_reserva={self.finalidade_reserva}, observacoes={self.observacoes}, "
            f"descricao={self.descricao}, id_reserva_semestre={self.id_reserva_semestre})"
        )

class Reservas_Temporarias(ReservaBase):
    __tablename__ = 'reservas_temporarias'

    id_reserva_temporaria: Mapped[int] = mapped_column(primary_key=True)
    inicio_reserva: Mapped[date] = mapped_column(nullable=False)
    fim_reserva: Mapped[date] = mapped_column(nullable=False)

    __table_args__ = (
        CheckConstraint(
            "inicio_reserva <= fim_reserva",
            name='chk_reserva_inicio_menor_fim'
        ),
    )

    pessoa: Mapped['Pessoas'] = relationship("Pessoas", back_populates="reservas_temporarias")
    usuario_especial: Mapped['Usuarios_Especiais'] = relationship("Usuarios_Especiais", back_populates="reservas_temporarias")
    local: Mapped['Locais'] = relationship("Locais", back_populates="reservas_temporarias")
    aula_ativa: Mapped['Aulas_Ativas'] = relationship("Aulas_Ativas", back_populates="reservas_temporarias")

    @property
    def selector_identification(self):
        local = self.local.nome_local
        aula = self.aula_ativa.selector_identification
        inicio = parse_date(self.inicio_reserva)
        fim = parse_date(self.fim_reserva)
        return f" {aula} em {local} de {inicio} ate {fim}"

    def __repr__(self):
        return (
            f"Reservas_Fixas(id_reserva_temporaria={self.id_reserva_temporaria}, id_responsavel={self.id_responsavel}, "
            f"id_responsavel_especial={self.id_responsavel_especial}, tipo_responsavel={self.tipo_responsavel}, "
            f"id_reserva_local={self.id_reserva_local}, id_reserva_aula={self.id_reserva_aula}, "
            f"finalidade_reserva={self.finalidade_reserva}, observacoes={self.observacoes}, "
            f"descricao={self.descricao}, inicio_reserva={self.inicio_reserva}, "
            f"fim_reserva={self.fim_reserva})"
        )

class Usuarios_Especiais(Base):
    __tablename__ = 'usuarios_especiais'

    id_usuario_especial: Mapped[int] = mapped_column(primary_key=True)
    nome_usuario_especial: Mapped[str] = mapped_column(String(100), nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='usuario_especial')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='usuario_especial')

    __table_args__ = (
        UniqueConstraint(
            'nome_usuario_especial',
            name='uq_usuario_especial'
        ),
    )

    def __repr__(self) -> str:
        return f"<Usuarios_Especiais(id_usuario_especial={self.id_usuario_especial}, nome_usuario_especial={self.nome_usuario_especial})>"

class Usuarios(Base):
    __tablename__ = 'usuarios'

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    tipo_pessoa: Mapped[str] = mapped_column(String(50), nullable=False)
    situacao_pessoa: Mapped[str] = mapped_column(String(50), nullable=False)
    grupo_pessoa: Mapped[str | None] = mapped_column(String(50))

    pessoa: Mapped['Pessoas'] = relationship(back_populates='usuarios')
    permissoes: Mapped[list['Permissoes']] = relationship(back_populates='usuario')
    historicos: Mapped[list['Historicos']] = relationship(back_populates='usuario')

    def __repr__(self) -> str:
        return (
            f"<Usuarios(id_usuario={self.id_usuario}, id_pessoa={self.id_pessoa}, "
            f"tipo_pessoa={self.tipo_pessoa}, situacao_pessoa={self.situacao_pessoa}, "
            f"grupo_pessoa={self.grupo_pessoa})>"
        )
    
    def __str__(self):
        uid = self.id_usuario
        pid = self.id_pessoa
        nome = self.pessoa.nome_pessoa
        return f"({uid}, {pid}) {nome}"

class Pessoas(Base):
    __tablename__ = 'pessoas'

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome_pessoa: Mapped[str] = mapped_column(String(100), nullable=False)
    email_pessoa: Mapped[str | None] = mapped_column(String(100))
    alias: Mapped[str | None] = mapped_column(String(100))

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='pessoa')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='pessoa')
    usuarios: Mapped[list['Usuarios']] = relationship(back_populates='pessoa')
    reservas_responsavel: Mapped[list['Reservas_Auditorios']] = relationship(
        back_populates="responsavel",
        foreign_keys="Reservas_Auditorios.id_responsavel"
    )
    reservas_autorizador: Mapped[list['Reservas_Auditorios']] = relationship(
        back_populates="autorizador",
        foreign_keys="Reservas_Auditorios.id_autorizador"
    )

    def __repr__(self) -> str:
        return (
            f"<Pessoas(id_pessoa={self.id_pessoa}, nome_pessoa={self.nome_pessoa}, "
            f"email_pessoa={self.email_pessoa})>"
        )

class Permissoes(Base):
    __tablename__ = 'permissoes'

    id_permissao_usuario: Mapped[int] = mapped_column(ForeignKey('usuarios.id_usuario'), primary_key=True)
    permissao: Mapped[int] = mapped_column(nullable=False)

    usuario: Mapped['Usuarios'] = relationship(back_populates='permissoes')

    def __repr__(self) -> str:
        return f"<Permissoes(id_permissao_usuario={self.id_permissao_usuario}, permissao={self.permissao})>"

class Locais(Base):
    __tablename__ = 'locais'

    id_local: Mapped[int] = mapped_column(primary_key=True)
    nome_local: Mapped[str] = mapped_column(String(100), nullable=False)
    descrição: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    disponibilidade: Mapped[DisponibilidadeEnum] = mapped_column(
        Enum(DisponibilidadeEnum, name="disponibilidade_enum", create_constraint=True),
        server_default=DisponibilidadeEnum.DISPONIVEL.name
    )

    tipo: Mapped[TipoLocalEnum] = mapped_column(
        Enum(TipoLocalEnum, name="tipo_local_enum", create_constraint=True),
        nullable=False,
        server_default=TipoLocalEnum.LABORATORIO.name
    )

    __table_args__ = (
        UniqueConstraint(
            'nome_local',
            name='uq_local'
        ),
    )

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='local')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='local')
    reservas_auditorios: Mapped[list['Reservas_Auditorios']] = relationship(back_populates='local')
    situacoes_das_reservas: Mapped[list['Situacoes_Das_Reserva']] = relationship(back_populates='local') 
    exibicao_reservas: Mapped[list['Exibicao_Reservas']] = relationship(back_populates='local')

    def __repr__(self) -> str:
        return (
            f"<Locais(id_local={self.id_local}, nome_local={self.nome_local}, "
            f"disponibilidade={self.disponibilidade.value}, tipo={self.tipo.value})>"
        )

class Aulas(Base):
    __tablename__ = 'aulas'

    id_aula: Mapped[int] = mapped_column(primary_key=True)
    horario_inicio: Mapped[time] = mapped_column(nullable=False)
    horario_fim: Mapped[time] = mapped_column(nullable=False)

    aulas_ativas: Mapped[list['Aulas_Ativas']] = relationship(back_populates='aula')

    __table_args__ = (
        UniqueConstraint(
            'horario_inicio',
            'horario_fim',
            name='uq_aula_inicio_fim'
        ),
    )

    @property
    def selector_identification(self):
        inicio = parse_time(self.horario_inicio)
        fim = parse_time(self.horario_fim)
        return f"{inicio} - {fim}"
    
    def __repr__(self) -> str:
        return (
            f"<Aulas(id_aula={self.id_aula}, horario_inicio={self.horario_inicio}, "
            f"horario_fim={self.horario_fim})>"
        )
    
class Dias_da_Semana(Base):
    __tablename__ = 'dias_da_semana'

    id_semana: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nome_semana: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)

    aulas_ativas: Mapped[list['Aulas_Ativas']] = relationship(back_populates='dia_da_semana')

    def __repr__(self) -> str:
        return f"<Dias_da_Semana(id_semana={self.id_semana}, nome_semana={self.nome_semana})>"

class Turnos(Base):
    __tablename__ = 'turnos'

    id_turno: Mapped[int] = mapped_column(primary_key=True)
    nome_turno: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    horario_inicio: Mapped[time] = mapped_column(nullable=False)
    horario_fim: Mapped[time] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'horario_inicio',
            'horario_fim',
            name='uq_turno_inicio_fim'
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Turnos(id_turno={self.id_turno}, nome_turno={self.nome_turno}, "
            f"horario_inicio={self.horario_inicio}, horario_fim={self.horario_fim})>"
        )

class Aulas_Ativas(Base):
    __tablename__ = 'aulas_ativas'

    id_aula_ativa: Mapped[int] = mapped_column(primary_key=True)
    id_aula: Mapped[int] = mapped_column(ForeignKey('aulas.id_aula'), nullable=False)
    inicio_ativacao: Mapped[date | None] = mapped_column()
    fim_ativacao: Mapped[date | None] = mapped_column()
    id_semana: Mapped[int] = mapped_column(ForeignKey('dias_da_semana.id_semana'), nullable=False)

    tipo_aula: Mapped[TipoAulaEnum] = mapped_column(
        Enum(TipoAulaEnum, name="tipo_aula_enum", create_constraint=True),
        server_default=TipoAulaEnum.AULA.name
    )

    @property
    def selector_identification(self):
        inicio = parse_date(self.inicio_ativacao)
        fim = parse_date(self.fim_ativacao)

        tipo = self.tipo_aula.value.capitalize()
        intervalo_aula = self.aula.selector_identification
        semana = self.dia_da_semana.nome_semana.capitalize()

        if inicio and fim:
            intervalo_ativacao = f"de {inicio} até {fim}"
        elif inicio:
            intervalo_ativacao = f"a partir de {inicio}"
        elif fim:
            intervalo_ativacao = f"até o dia {fim}"
        else:
            intervalo_ativacao = "por um período indeterminado"

        if semana.lower() in ['sabado', 'domingo']:
            artigo = 'no'
        else:
            artigo = 'na'

        return f"{tipo}: {intervalo_aula} {artigo} {semana} (ativa:{intervalo_ativacao})"

    __table_args__ = (
        CheckConstraint(
            'inicio_ativacao IS NULL OR fim_ativacao IS NULL OR inicio_ativacao <= fim_ativacao',
            name='chk_aula_ativa_inicio_menor_fim'
        ), UniqueConstraint(
            'id_aula',
            'id_semana',
            'tipo_aula',
            name='unique_aula_semana_tipo'
        )
    )

    aula: Mapped['Aulas'] = relationship(back_populates='aulas_ativas')
    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='aula_ativa')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='aula_ativa')
    reservas_auditorios: Mapped[list['Reservas_Auditorios']] = relationship(back_populates='aula_ativa')
    situacoes_das_reservas: Mapped[list['Situacoes_Das_Reserva']] = relationship(back_populates='aula_ativa')
    exibicao_reservas: Mapped[list['Exibicao_Reservas']] = relationship(back_populates='aula_ativa')
    dia_da_semana: Mapped['Dias_da_Semana'] = relationship(back_populates='aulas_ativas')

    def __repr__(self) -> str:
        return (
            f"<Aulas_Ativas(id_aula_ativa={self.id_aula_ativa}, id_aula={self.id_aula}, "
            f"inicio_ativacao={self.inicio_ativacao}, fim_ativacao={self.fim_ativacao}, "
            f"id_semana={self.id_semana}, tipo_aula={self.tipo_aula})>"
        )

class Historicos(Base):
    __tablename__ = 'historicos'

    id_historico: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey('usuarios.id_usuario'), nullable=True)
    tabela: Mapped[str | None] = mapped_column(String(100), index=True)
    categoria: Mapped[str | None] = mapped_column(String(100))
    data_hora: Mapped[datetime] = mapped_column(index=True, nullable=False)
    message: Mapped[str] = mapped_column(TEXT, nullable=False)
    chave_primaria: Mapped[str] = mapped_column(TEXT, nullable=False)
    observacao: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    origem: Mapped[OrigemEnum] = mapped_column(
        Enum(OrigemEnum, name="origem_enum", create_constraint=True),
        server_default=OrigemEnum.SISTEMA.name
    )

    usuario: Mapped['Usuarios'] = relationship(back_populates='historicos')

    def __repr__(self) -> str:
        return (
            f"<Historicos(id_historico={self.id_historico}, id_usuario={self.id_usuario}, "
            f"tabela={self.tabela}, categoria={self.categoria}, "
            f"data_hora={self.data_hora}, message={self.message}, "
            f"chave_primaria={self.chave_primaria}, observacao={self.observacao})>"
        )

class Semestres(Base):
    __tablename__ = 'semestres'

    id_semestre: Mapped[int] = mapped_column(primary_key=True)
    nome_semestre: Mapped[str] = mapped_column(String(100), nullable=False)
    data_inicio: Mapped[date] = mapped_column(nullable=False)
    data_fim: Mapped[date] = mapped_column(nullable=False)
    data_inicio_reserva: Mapped[date] = mapped_column(nullable=False)
    data_fim_reserva: Mapped[date] = mapped_column(nullable=False)
    dias_de_prioridade: Mapped[int] = mapped_column(nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='semestre')

    __table_args__ = (
        UniqueConstraint(
            'data_inicio_reserva',
            'data_fim_reserva',
            name='uq_semestre_inicio_fim_reserva'
        ), UniqueConstraint(
            'data_inicio',
            'data_fim',
            name='uq_semestre_inicio_fim'
        ), UniqueConstraint(
            'nome_semestre',
            name='uq_semestre_nome'
        )
    )

    def __repr__(self) -> str:
        return (
            f"<Semestres(id_semestre={self.id_semestre}, nome_semestre={self.nome_semestre}, "
            f"data_inicio={self.data_inicio}, data_fim={self.data_fim}, "
            f"data_inicio_reserva={self.data_inicio_reserva}, data_fim_reserva={self.data_fim_reserva}, "
            f"dias_de_prioridade={self.dias_de_prioridade})>"
        )