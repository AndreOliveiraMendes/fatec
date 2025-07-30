import enum
from datetime import date, datetime, time

from sqlalchemy import (TEXT, CheckConstraint, Enum, ForeignKey, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


def parse_time(time):
    return time.strftime('%H:%M') if time else None

def parse_date(date):
    return date.strftime('%d/%m/%Y') if date else None

class SituacaoChaveEnum(enum.Enum):
    NAO_PEGOU_A_CHAVE = "não pegou a chave"
    PEGOU_A_CHAVE = "pegou a chave"
    DEVOLVEU_A_CHAVE = "devolveu a chave"

class Situacoes_Das_Reserva(db.Model):
    __tablename__ = "situacoes_das_reservas"

    id_situacao:Mapped[int] = mapped_column(primary_key=True)
    id_situacao_laboratorio:Mapped[int] = mapped_column(ForeignKey("laboratorios.id_laboratorio"), nullable=False)
    id_situacao_aula:Mapped[int] = mapped_column(ForeignKey("aulas_ativas.id_aula_ativa"), nullable=False)
    situacao_dia:Mapped[date] = mapped_column(nullable=False)

    situacao_chave: Mapped[SituacaoChaveEnum] = mapped_column(
        Enum(SituacaoChaveEnum, name="situacao_chave_enum", create_constraint=True),
        server_default=SituacaoChaveEnum.NAO_PEGOU_A_CHAVE.name
    )

    __table_args__ = (
        UniqueConstraint(
            'id_situacao_laboratorio',
            'id_situacao_aula',
            'situacao_dia',
            name="uq_situacao_lab_aula_dia"
        ),
    )

    laboratorios: Mapped['Laboratorios'] = relationship(back_populates='situacoes_das_reservas')
    aulas_ativas: Mapped['Aulas_Ativas'] = relationship(back_populates='situacoes_das_reservas')

    @property
    def selector_identification(self):
        aula = self.aulas_ativas.selector_identification
        laboratorio = self.laboratorios.nome_laboratorio
        dia = parse_date(self.situacao_dia)
        return f" {dia} no {laboratorio} as {aula}"

    def __repr__(self) -> str:
        return (
            f"<SituacaoReserva(id_situacao={self.id_situacao}, id_situacao_laboratorio={self.id_situacao_laboratorio}, "
            f"id_situacao_aula={self.id_situacao_aula}, situacao_dia={self.situacao_dia} "
            f"situacao_chave={self.situacao_chave.value})>"
        )

class TipoReservaEnum(enum.Enum):
    GRADUACAO = "Graduação"
    ESPECIALIZACAO = "Especialização"
    EAD = "EAD"
    NAPTI = "NAPTI"
    CURSO = "Curso"
    USO_DOS_ALUNOS = "Uso dos Alunos"

class Reservas_Fixas(db.Model):
    __tablename__ = 'reservas_fixas'

    id_reserva_fixa: Mapped[int] = mapped_column(primary_key=True)
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    id_responsavel_especial: Mapped[int | None] = mapped_column(ForeignKey('usuarios_especiais.id_usuario_especial'), nullable=True)
    tipo_responsavel: Mapped[int] = mapped_column(nullable=False)
    id_reserva_laboratorio: Mapped[int] = mapped_column(ForeignKey('laboratorios.id_laboratorio'), nullable=False)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    id_reserva_semestre: Mapped[int] = mapped_column(ForeignKey('semestres.id_semestre'), nullable=False)

    tipo_reserva: Mapped[TipoReservaEnum] = mapped_column(
        Enum(TipoReservaEnum, name="tipo_reserva_enum", create_constraint=True),
        server_default=TipoReservaEnum.GRADUACAO.name
    )

    __table_args__ = (
        CheckConstraint(
            """
            (
                (tipo_responsavel = 0 AND id_responsavel IS NOT NULL AND id_responsavel_especial IS NULL)
                OR
                (tipo_responsavel = 1 AND id_responsavel IS NULL AND id_responsavel_especial IS NOT NULL)
                OR
                (tipo_responsavel = 2 AND id_responsavel IS NOT NULL AND id_responsavel_especial IS NOT NULL)
            )
            """,
            name='check_tipo_responsavel_fixa'
        ), CheckConstraint(
            """
            tipo_responsavel IN (0,1,2)
            """,
            name='check_tipo_responsavel_value_fixa'
        ), UniqueConstraint(
            'id_reserva_laboratorio',
            'id_reserva_aula',
            'id_reserva_semestre',
            name='uq_reserva_lab_aula_semestre'
        )
    )

    pessoas: Mapped['Pessoas'] = relationship(back_populates='reservas_fixas')
    usuarios_especiais: Mapped['Usuarios_Especiais'] = relationship(back_populates='reservas_fixas')
    laboratorios: Mapped['Laboratorios'] = relationship(back_populates='reservas_fixas')
    aulas_ativas: Mapped['Aulas_Ativas'] = relationship(back_populates='reservas_fixas')
    semestres: Mapped['Semestres'] = relationship(back_populates='reservas_fixas')

    @property
    def selector_identification(self):
        laboratorio = self.laboratorios.nome_laboratorio
        aula = self.aulas_ativas.selector_identification
        semestre = self.semestres.nome_semestre
        return f" {aula} em {laboratorio} no {semestre}"

    def __repr__(self) -> str:
        return (
            f"<Reservas_Fixas(id_reserva_fixa={self.id_reserva_fixa}, id_responsavel={self.id_responsavel}, "
            f"id_responsavel_especial={self.id_responsavel_especial}, tipo_responsavel={self.tipo_responsavel}, "
            f"id_reserva_laboratorio={self.id_reserva_laboratorio}, id_reserva_aula={self.id_reserva_aula}, "
            f"tipo_reserva={self.tipo_reserva}, id_reserva_semestre={self.id_reserva_semestre})>"
        )

class Reservas_Temporarias(db.Model):
    __tablename__ = 'reservas_temporarias'

    id_reserva_temporaria: Mapped[int] = mapped_column(primary_key=True)
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    id_responsavel_especial: Mapped[int | None] = mapped_column(ForeignKey('usuarios_especiais.id_usuario_especial'), nullable=True)
    tipo_responsavel: Mapped[int] = mapped_column(nullable=False)
    id_reserva_laboratorio: Mapped[int] = mapped_column(ForeignKey('laboratorios.id_laboratorio'), nullable=False)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    inicio_reserva: Mapped[date] = mapped_column(nullable=False)
    fim_reserva: Mapped[date] = mapped_column(nullable=False)

    tipo_reserva: Mapped[TipoReservaEnum] = mapped_column(
        Enum(TipoReservaEnum, name="tipo_reserva_enum", create_constraint=True),
        server_default=TipoReservaEnum.GRADUACAO.name
    )

    __table_args__ = (
        CheckConstraint(
            """
            (
                (tipo_responsavel = 0 AND id_responsavel IS NOT NULL AND id_responsavel_especial IS NULL)
                OR
                (tipo_responsavel = 1 AND id_responsavel IS NULL AND id_responsavel_especial IS NOT NULL)
                OR
                (tipo_responsavel = 2 AND id_responsavel IS NOT NULL AND id_responsavel_especial IS NOT NULL)
            )
            """,
            name='check_tipo_responsavel_temporaria'
        ), CheckConstraint(
            """
            tipo_responsavel IN (0,1,2)
            """,
            name='check_tipo_responsavel_value_temporaria'
        ), CheckConstraint(
            "inicio_reserva <= fim_reserva",
            name='chk_reserva_inicio_menor_fim'
        )
    )

    pessoas: Mapped['Pessoas'] = relationship(back_populates='reservas_temporarias')
    usuarios_especiais: Mapped['Usuarios_Especiais'] = relationship(back_populates='reservas_temporarias')
    laboratorios: Mapped['Laboratorios'] = relationship(back_populates='reservas_temporarias')
    aulas_ativas: Mapped['Aulas_Ativas'] = relationship(back_populates='reservas_temporarias')

    @property
    def selector_identification(self):
        laboratorio = self.laboratorios.nome_laboratorio
        aula = self.aulas_ativas.selector_identification
        inicio = parse_date(self.inicio_reserva)
        fim = parse_date(self.fim_reserva)
        return f" {aula} em {laboratorio} de {inicio} ate {fim}"

    def __repr__(self) -> str:
        return (
            f"<Reservas_Fixas(id_reserva_fixa={self.id_reserva_temporaria}, id_responsavel={self.id_responsavel}, "
            f"id_responsavel_especial={self.id_responsavel_especial}, tipo_responsavel={self.tipo_responsavel}, "
            f"id_reserva_laboratorio={self.id_reserva_laboratorio}, id_reserva_aula={self.id_reserva_aula}, "
            f"tipo_reserva={self.tipo_reserva}, inicio_reserva={self.inicio_reserva}, "
            f"fim_reserva={self.fim_reserva})>"
        )

class Usuarios_Especiais(db.Model):
    __tablename__ = 'usuarios_especiais'

    id_usuario_especial: Mapped[int] = mapped_column(primary_key=True)
    nome_usuario_especial: Mapped[str] = mapped_column(String(100), nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='usuarios_especiais')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='usuarios_especiais')

    __table_args__ = (
        UniqueConstraint(
            'nome_usuario_especial',
            name='uq_usuario_especial'
        ),
    )

    def __repr__(self) -> str:
        return f"<Usuarios_Especiais(id_usuario_especial={self.id_usuario_especial}, nome_usuario_especial={self.nome_usuario_especial})>"

    
class Usuarios(db.Model):
    __tablename__ = 'usuarios'

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    tipo_pessoa: Mapped[str] = mapped_column(String(50), nullable=False)
    situacao_pessoa: Mapped[str] = mapped_column(String(50), nullable=False)
    grupo_pessoa: Mapped[str | None] = mapped_column(String(50))

    pessoas: Mapped['Pessoas'] = relationship(back_populates='usuarios')
    permissoes: Mapped[list['Permissoes']] = relationship(back_populates='usuarios')
    historicos: Mapped[list['Historicos']] = relationship(back_populates='usuarios')

    def __repr__(self) -> str:
        return (
            f"<Usuarios(id_usuario={self.id_usuario}, id_pessoa={self.id_pessoa}, "
            f"tipo_pessoa={self.tipo_pessoa}, situacao_pessoa={self.situacao_pessoa}, "
            f"grupo_pessoa={self.grupo_pessoa})>"
        )
    
    def __str__(self):
        uid = self.id_usuario
        pid = self.id_pessoa
        nome = self.pessoas.nome_pessoa
        return f"({uid}, {pid}) {nome}"

class Pessoas(db.Model):
    __tablename__ = 'pessoas'

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome_pessoa: Mapped[str] = mapped_column(String(100), nullable=False)
    email_pessoa: Mapped[str | None] = mapped_column(String(100))

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='pessoas')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='pessoas')
    usuarios: Mapped[list['Usuarios']] = relationship(back_populates='pessoas')

    def __repr__(self) -> str:
        return (
            f"<Pessoas(id_pessoa={self.id_pessoa}, nome_pessoa={self.nome_pessoa}, "
            f"email_pessoa={self.email_pessoa})>"
        )

class Permissoes(db.Model):
    __tablename__ = 'permissoes'

    id_permissao_usuario: Mapped[int] = mapped_column(ForeignKey('usuarios.id_usuario'), primary_key=True)
    permissao: Mapped[int] = mapped_column(nullable=False)

    usuarios: Mapped['Usuarios'] = relationship(back_populates='permissoes')

    def __repr__(self) -> str:
        return f"<Permissoes(id_permissao_usuario={self.id_permissao_usuario}, permissao={self.permissao})>"

class DisponibilidadeEnum(enum.Enum):
    DISPONIVEL = "Disponivel"
    INDISPONIVEL = "Indisponivel"

class TipoLaboratorioEnum(enum.Enum):
    LABORATORIO = "Laboratório"
    SALA = "Sala"
    EXTERNO = "Externo"

class Laboratorios(db.Model):
    __tablename__ = 'laboratorios'

    id_laboratorio: Mapped[int] = mapped_column(primary_key=True)
    nome_laboratorio: Mapped[str] = mapped_column(String(100), nullable=False)

    disponibilidade: Mapped[DisponibilidadeEnum] = mapped_column(
        Enum(DisponibilidadeEnum, name="disponibilidade_enum", create_constraint=True),
        server_default=DisponibilidadeEnum.DISPONIVEL.name
    )

    tipo: Mapped[TipoLaboratorioEnum] = mapped_column(
        Enum(TipoLaboratorioEnum, name="tipo_laboratorio_enum", create_constraint=True),
        nullable=False,
        server_default=TipoLaboratorioEnum.LABORATORIO.name
    )

    __table_args__ = (
        UniqueConstraint(
            'nome_laboratorio',
            name='uq_laboratorio'
        ),
    )

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='laboratorios')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='laboratorios')
    situacoes_das_reservas: Mapped[list['Situacoes_Das_Reserva']] = relationship(back_populates='laboratorios') 

    def __repr__(self) -> str:
        return (
            f"<Laboratorios(id_laboratorio={self.id_laboratorio}, nome_laboratorio={self.nome_laboratorio}, "
            f"disponibilidade={self.disponibilidade.value}, tipo={self.tipo.value})>"
        )

class Aulas(db.Model):
    __tablename__ = 'aulas'

    id_aula: Mapped[int] = mapped_column(primary_key=True)
    horario_inicio: Mapped[time] = mapped_column(nullable=False)
    horario_fim: Mapped[time] = mapped_column(nullable=False)

    aulas_ativas: Mapped[list['Aulas_Ativas']] = relationship(back_populates='aulas')

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
    
class Dias_da_Semana(db.Model):
    __tablename__ = 'dias_da_semana'

    id_semana: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nome_semana: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)

    aulas_ativas: Mapped[list['Aulas_Ativas']] = relationship(back_populates='dia_da_semana')

    def __repr__(self) -> str:
        return f"<Dias_da_Semana(id_semana={self.id_semana}, nome_semana={self.nome_semana})>"


class Turnos(db.Model):
    __tablename__ = 'turnos'

    id_turno: Mapped[int] = mapped_column(primary_key=True)
    nome_turno: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
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
    
class TipoAulaEnum(enum.Enum):
    AULA = "Aula"
    EVENTO = "Evento"
    OUTROS = "Outros"

class Aulas_Ativas(db.Model):
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
        intervalo_aula = self.aulas.selector_identification
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

    aulas: Mapped['Aulas'] = relationship(back_populates='aulas_ativas')
    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='aulas_ativas')
    reservas_temporarias: Mapped[list['Reservas_Temporarias']] = relationship(back_populates='aulas_ativas')
    situacoes_das_reservas: Mapped[list['Situacoes_Das_Reserva']] = relationship(back_populates='aulas_ativas')

    dia_da_semana: Mapped['Dias_da_Semana'] = relationship(back_populates='aulas_ativas')

    def __repr__(self) -> str:
        return (
            f"<Aulas_Ativas(id_aula_ativa={self.id_aula_ativa}, id_aula={self.id_aula}, "
            f"inicio_ativacao={self.inicio_ativacao}, fim_ativacao={self.fim_ativacao}, "
            f"id_semana={self.id_semana}, tipo_aula={self.tipo_aula})>"
        )
    
class OrigemEnum(enum.Enum):
    SISTEMA = "Sistema"
    USUARIO = "Usuario"

class Historicos(db.Model):
    __tablename__ = 'historicos'

    id_historico: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey('usuarios.id_usuario'), nullable=True)
    tabela: Mapped[str | None] = mapped_column(String(100), index=True)
    categoria: Mapped[str | None] = mapped_column(String(100))
    data_hora: Mapped[datetime] = mapped_column(index=True, nullable=False)
    message: Mapped[str] = mapped_column(TEXT, nullable=False)
    chave_primaria: Mapped[str] = mapped_column(TEXT, nullable=False)
    observacao: Mapped[str | None] = mapped_column(TEXT)

    origem: Mapped[OrigemEnum] = mapped_column(
        Enum(OrigemEnum, name="origem_enum", create_constraint=True),
        server_default=OrigemEnum.SISTEMA.name
    )

    usuarios: Mapped['Usuarios'] = relationship(back_populates='historicos')

    def __repr__(self) -> str:
        return (
            f"<Historicos(id_historico={self.id_historico}, id_usuario={self.id_usuario}, "
            f"tabela={self.tabela}, categoria={self.categoria}, "
            f"data_hora={self.data_hora}, message={self.message}, "
            f"chave_primaria={self.chave_primaria}, observacao={self.observacao})>"
        )

class Semestres(db.Model):
    __tablename__ = 'semestres'

    id_semestre: Mapped[int] = mapped_column(primary_key=True)
    nome_semestre: Mapped[str] = mapped_column(String(100), nullable=False)
    data_inicio: Mapped[date] = mapped_column(nullable=False)
    data_fim: Mapped[date] = mapped_column(nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='semestres')

    __table_args__ = (
        UniqueConstraint(
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
            f"data_inicio={self.data_inicio}, data_fim={self.data_fim})>"
        )