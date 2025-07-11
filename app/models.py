import enum
from app import db
from datetime import date, time, datetime
from sqlalchemy import String, ForeignKey, CheckConstraint, TEXT, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Reservas_Fixas(db.Model):
    __tablename__ = 'reservas_fixas'

    id_reserva_fixa: Mapped[int] = mapped_column(primary_key=True)
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    id_responsavel_especial: Mapped[int | None] = mapped_column(ForeignKey('usuarios_especiais.id_usuario_especial'), nullable=True)
    tipo_responsavel: Mapped[int] = mapped_column(nullable=False)
    id_reserva_laboratorio: Mapped[int] = mapped_column(ForeignKey('laboratorios.id_laboratorio'), nullable=False)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    status_reserva: Mapped[int] = mapped_column(server_default='0', nullable=False)
    tipo_reserva: Mapped[int] = mapped_column(server_default='0', nullable=False)
    id_reserva_semestre: Mapped[int] = mapped_column(ForeignKey('semestres.id_semestre'), nullable=False)

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
            name='check_tipo_responsavel'
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
    
    def __repr__(self) -> str:
        return (
            f"<Reservas_Fixas(id_reserva_fixa={self.id_reserva_fixa}, id_responsavel={self.id_responsavel}, "
            f"id_responsavel_especial={self.id_responsavel_especial}, tipo_responsavel={self.tipo_responsavel}, "
            f"id_reserva_laboratorio={self.id_reserva_laboratorio}, id_reserva_aula={self.id_reserva_aula}, "
            f"status_reserva={self.status_reserva}, tipo_reserva={self.tipo_reserva}, "
            f"id_reserva_semestre={self.id_reserva_semestre})>"
        )

class Usuarios_Especiais(db.Model):
    __tablename__ = 'usuarios_especiais'

    id_usuario_especial: Mapped[int] = mapped_column(primary_key=True)
    nome_usuario_especial: Mapped[str] = mapped_column(String(100), nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='usuarios_especiais')

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

class Pessoas(db.Model):
    __tablename__ = 'pessoas'

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome_pessoa: Mapped[str] = mapped_column(String(100), nullable=False)
    email_pessoa: Mapped[str | None] = mapped_column(String(100))

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='pessoas')
    usuarios: Mapped[list['Usuarios']] = relationship(back_populates='pessoas')
    historicos: Mapped[list['Historicos']] = relationship(back_populates='pessoas')

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
        server_default=DisponibilidadeEnum.DISPONIVEL.value
    )

    tipo: Mapped[TipoLaboratorioEnum] = mapped_column(
        Enum(TipoLaboratorioEnum, name="tipo_laboratorio_enum", create_constraint=True),
        nullable=False,
        server_default=TipoLaboratorioEnum.LABORATORIO.value
    )

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='laboratorios')

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

    @property
    def horario_intervalo(self):
        return f"{self.horario_inicio.strftime('%H:%M')} - {self.horario_fim.strftime('%H:%M')}"
    
    def __repr__(self) -> str:
        return (
            f"<Aulas(id_aula={self.id_aula}, horario_inicio={self.horario_inicio}, "
            f"horario_fim={self.horario_fim})>"
        )
    
class Dias_da_Semana(db.Model):
    __tablename__ = 'dias_da_semana'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nome: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)

    aulas_ativas: Mapped[list['Aulas_Ativas']] = relationship(back_populates='dia_da_semana')

    def __repr__(self) -> str:
        return f"<Dias_da_Semana(id={self.id}, nome={self.nome})>"


class Turnos(db.Model):
    __tablename__ = 'turnos'

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    horario_inicio: Mapped[time] = mapped_column(nullable=False)
    horario_fim: Mapped[time] = mapped_column(nullable=False)

    aulas_ativas: Mapped[list['Aulas_Ativas']] = relationship(back_populates='turno_info')

    def __repr__(self) -> str:
        return (
            f"<Turnos(id={self.id}, nome={self.nome}, "
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
    id_semana: Mapped[int] = mapped_column(ForeignKey('dias_da_semana.id'), nullable=False)
    id_turno: Mapped[int] = mapped_column(ForeignKey('turnos.id'), nullable=False)

    tipo_aula: Mapped[TipoAulaEnum] = mapped_column(
        Enum(TipoAulaEnum, name="tipoaula_enum", create_constraint=True),
        server_default=TipoAulaEnum.AULA.value
    )
    #inicio, fim, aula, semana, turno, tipo

    @property    
    def selector_indentification(self):
        return f"({self.id_aula}) ({self.id_semana}) ({self.id_turno}) {self.tipo_aula.value}:{self.inicio_ativacao} - {self.fim_ativacao}"

    __table_args__ = (
        CheckConstraint(
            'inicio_ativacao IS NULL OR fim_ativacao IS NULL OR inicio_ativacao <= fim_ativacao',
            name='chk_inicio_menor_fim'
        ),
    )

    aulas: Mapped['Aulas'] = relationship(back_populates='aulas_ativas')
    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='aulas_ativas')

    dia_da_semana: Mapped['Dias_da_Semana'] = relationship(back_populates='aulas_ativas')
    turno_info: Mapped['Turnos'] = relationship(back_populates='aulas_ativas')

    def __repr__(self) -> str:
        return (
            f"<Aulas_Ativas(id_aula_ativa={self.id_aula_ativa}, id_aula={self.id_aula}, "
            f"inicio_ativacao={self.inicio_ativacao}, fim_ativacao={self.fim_ativacao}, "
            f"id_semana={self.id_semana}, id_turno={self.id_turno}, "
            f"tipo_aula={self.tipo_aula})>"
        )

class Historicos(db.Model):
    __tablename__ = 'historicos'

    id_historico: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey('usuarios.id_usuario'), nullable=False)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    tabela: Mapped[str | None] = mapped_column(String(100), index=True)
    categoria: Mapped[str | None] = mapped_column(String(100))
    data_hora: Mapped[datetime] = mapped_column(index=True, nullable=False)
    message: Mapped[str] = mapped_column(TEXT, nullable=False)
    chave_primaria: Mapped[str] = mapped_column(TEXT, nullable=False)
    observacao: Mapped[str | None] = mapped_column(TEXT)

    usuarios: Mapped['Usuarios'] = relationship(back_populates='historicos')
    pessoas: Mapped['Pessoas'] = relationship(back_populates='historicos')

    def __repr__(self) -> str:
        return (
            f"<Historicos(id_historico={self.id_historico}, id_usuario={self.id_usuario}, "
            f"id_pessoa={self.id_pessoa}, tabela={self.tabela}, "
            f"categoria={self.categoria}, data_hora={self.data_hora}, "
            f"message={self.message}, chave_primaria={self.chave_primaria}, "
            f"observacao={self.observacao})>"
        )

class Semestres(db.Model):
    __tablename__ = 'semestres'

    id_semestre: Mapped[int] = mapped_column(primary_key=True)
    nome_semestre: Mapped[str] = mapped_column(String(100), nullable=False)
    data_inicio: Mapped[date] = mapped_column(nullable=False)
    data_fim: Mapped[date] = mapped_column(nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='semestres')

    def __repr__(self) -> str:
        return (
            f"<Semestres(id_semestre={self.id_semestre}, nome_semestre={self.nome_semestre}, "
            f"data_inicio={self.data_inicio}, data_fim={self.data_fim})>"
        )