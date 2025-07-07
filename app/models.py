import enum
from flask import Blueprint
from app.main import db
from datetime import date, time, datetime
from sqlalchemy import String, ForeignKey, CheckConstraint, TEXT, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

bp = Blueprint("auth", __name__)

class Reservas_Fixas(db.Model):
    __tablename__ = 'reservas_fixas'

    id_reserva_fixa: Mapped[int] = mapped_column(primary_key=True)
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    id_responsavel_especial: Mapped[int | None] = mapped_column(ForeignKey('usuarios_especiais.id_usuario_especial'), nullable=True)
    tipo_responsavel: Mapped[int] = mapped_column(nullable=False)
    id_reserva_laboratorio: Mapped[int] = mapped_column(ForeignKey('laboratorios.id_laboratorio'), nullable=False)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    status_reserva: Mapped[int] = mapped_column(server_default='0', nullable=False)
    tipo: Mapped[int] = mapped_column(server_default='0', nullable=False)
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

class Usuarios_Especiais(db.Model):
    __tablename__ = 'usuarios_especiais'

    id_usuario_especial: Mapped[int] = mapped_column(primary_key=True)
    nome_usuario_especial: Mapped[str] = mapped_column(String(100), nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='usuarios_especiais')
    
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

class Pessoas(db.Model):
    __tablename__ = 'pessoas'

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome_pessoa: Mapped[str] = mapped_column(String(100), nullable=False)
    email_pessoa: Mapped[str | None] = mapped_column(String(100))

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='pessoas')
    usuarios: Mapped[list['Usuarios']] = relationship(back_populates='pessoas')
    historicos: Mapped[list['Historicos']] = relationship(back_populates='pessoas')

class Permissoes(db.Model):
    __tablename__ = 'permissoes'

    id_permissao_usuario: Mapped[int] = mapped_column(ForeignKey('usuarios.id_usuario'), primary_key=True)
    permissao: Mapped[int] = mapped_column(nullable=False)

    usuarios: Mapped['Usuarios'] = relationship(back_populates='permissoes')

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

class Aulas(db.Model):
    __tablename__ = 'aulas'

    id_aula: Mapped[int] = mapped_column(primary_key=True)
    horario_inicio: Mapped[time] = mapped_column(nullable=False)
    horario_fim: Mapped[time] = mapped_column(nullable=False)

    aulas_ativas: Mapped[list['Aulas_Ativas']] = relationship(back_populates='aulas')

    @property
    def horario_intervalo(self):
        return f"{self.horario_inicio.strftime('%H:%M')} - {self.horario_fim.strftime('%H:%M')}"

class Aulas_Ativas(db.Model):
    __tablename__ = 'aulas_ativas'

    id_aula_ativa: Mapped[int] = mapped_column(primary_key=True)
    id_aula: Mapped[int] = mapped_column(ForeignKey('aulas.id_aula'), nullable=False)
    inicio_ativacao: Mapped[date | None] = mapped_column()
    fim_ativacao: Mapped[date | None] = mapped_column()
    semana: Mapped[int | None] = mapped_column()
    turno: Mapped[int | None] = mapped_column()
    tipo_aula: Mapped[int] = mapped_column(server_default='0', nullable=False)

    aulas: Mapped['Aulas'] = relationship(back_populates='aulas_ativas')
    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='aulas_ativas')

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

class Semestres(db.Model):
    __tablename__ = 'semestres'

    id_semestre: Mapped[int] = mapped_column(primary_key=True)
    data_inicio: Mapped[date] = mapped_column(nullable=False)
    data_fim: Mapped[date] = mapped_column(nullable=False)

    reservas_fixas: Mapped[list['Reservas_Fixas']] = relationship(back_populates='semestres')