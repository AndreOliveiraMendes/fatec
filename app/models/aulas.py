from datetime import date, time

from sqlalchemy import (CheckConstraint, Enum, ForeignKey, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auxiliar.auxiliar_model import parse_date, parse_time
from app.enums import (TipoAulaEnum)
from app.extensions import Base

class Aulas(Base):
    __tablename__ = 'aulas'

    id_aula: Mapped[int] = mapped_column(primary_key=True)
    horario_inicio: Mapped[time] = mapped_column(nullable=False)
    horario_fim: Mapped[time] = mapped_column(nullable=False)

    aulas_ativas: Mapped[list["Aulas_Ativas"]] = relationship(back_populates='aula')

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
        ),
    )

    aula: Mapped["Aulas"] = relationship(back_populates='aulas_ativas')
    reservas_fixas: Mapped[list["Reservas_Fixas"]] = relationship(back_populates='aula_ativa')
    reservas_temporarias: Mapped[list["Reservas_Temporarias"]] = relationship(back_populates='aula_ativa')
    reservas_auditorios: Mapped[list["Reservas_Auditorios"]] = relationship(back_populates='aula_ativa')
    situacoes_das_reservas: Mapped[list["Situacoes_Das_Reserva"]] = relationship(back_populates='aula_ativa')
    exibicao_reservas: Mapped[list["Exibicao_Reservas"]] = relationship(back_populates='aula_ativa')
    dia_da_semana: Mapped["Dias_da_Semana"] = relationship(back_populates='aulas_ativas')

    def __repr__(self) -> str:
        return (
            f"<Aulas_Ativas(id_aula_ativa={self.id_aula_ativa}, id_aula={self.id_aula}, "
            f"inicio_ativacao={self.inicio_ativacao}, fim_ativacao={self.fim_ativacao}, "
            f"id_semana={self.id_semana}, tipo_aula={self.tipo_aula})>"
        )
    
class Dias_da_Semana(Base):
    __tablename__ = 'dias_da_semana'

    id_semana: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nome_semana: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)

    aulas_ativas: Mapped[list["Aulas_Ativas"]] = relationship(back_populates='dia_da_semana')

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
    
class Semestres(Base):
    __tablename__ = 'semestres'

    id_semestre: Mapped[int] = mapped_column(primary_key=True)
    nome_semestre: Mapped[str] = mapped_column(String(100), nullable=False)
    data_inicio: Mapped[date] = mapped_column(nullable=False)
    data_fim: Mapped[date] = mapped_column(nullable=False)
    data_inicio_reserva: Mapped[date] = mapped_column(nullable=False)
    data_fim_reserva: Mapped[date] = mapped_column(nullable=False)
    dias_de_prioridade: Mapped[int] = mapped_column(nullable=False)

    reservas_fixas: Mapped[list["Reservas_Fixas"]] = relationship(back_populates='semestre')

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