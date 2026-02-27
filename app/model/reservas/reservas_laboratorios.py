from datetime import date

from sqlalchemy import (TEXT, CheckConstraint, Enum, ForeignKey, String,
                        UniqueConstraint)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auxiliar.auxiliar_model import parse_date
from app.enums import (FinalidadeReservaEnum, TipoReservaEnum)
from app.extensions import Base

class ReservaBase(Base):
    __abstract__ = True
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
        elif self.id_responsavel is None and self.id_responsavel_especial is not None:
            return 1
        elif self.id_responsavel is not None and self.id_responsavel_especial is not None:
            return 2
        else:
            return 3

    @property
    def tipo_reserva_str(self) -> TipoReservaEnum:
        raise NotImplementedError

class Reservas_Fixas(ReservaBase):
    __tablename__ = 'reservas_fixas'

    id_reserva_fixa: Mapped[int] = mapped_column(primary_key=True)
    id_reserva_semestre: Mapped[int] = mapped_column(ForeignKey('semestres.id_semestre'), nullable=False)

    semestre: Mapped["Semestres"] = relationship(back_populates='reservas_fixas')

    __table_args__ = (
        UniqueConstraint(
            'id_reserva_local',
            'id_reserva_aula',
            'id_reserva_semestre',
            name='uq_reserva_local_aula_semestre'
        ),
    )

    pessoa: Mapped["Pessoas"] = relationship("Pessoas", back_populates="reservas_fixas")
    usuario_especial: Mapped["Usuarios_Especiais"] = relationship("Usuarios_Especiais", back_populates="reservas_fixas")
    local: Mapped["Locais"] = relationship("Locais", back_populates="reservas_fixas")
    aula_ativa: Mapped["Aulas_Ativas"] = relationship("Aulas_Ativas", back_populates="reservas_fixas")

    @property
    def selector_identification(self):
        local = self.local.nome_local
        aula = self.aula_ativa.selector_identification
        semestre = self.semestre.nome_semestre
        return f" {aula} em {local} no {semestre}"
    
    @property
    def tipo_reserva_str(self):
        return TipoReservaEnum.FIXA
    
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

    pessoa: Mapped["Pessoas"] = relationship("Pessoas", back_populates="reservas_temporarias")
    usuario_especial: Mapped["Usuarios_Especiais"] = relationship("Usuarios_Especiais", back_populates="reservas_temporarias")
    local: Mapped["Locais"] = relationship("Locais", back_populates="reservas_temporarias")
    aula_ativa: Mapped["Aulas_Ativas"] = relationship("Aulas_Ativas", back_populates="reservas_temporarias")

    @property
    def selector_identification(self):
        local = self.local.nome_local
        aula = self.aula_ativa.selector_identification
        inicio = parse_date(self.inicio_reserva)
        fim = parse_date(self.fim_reserva)
        return f" {aula} em {local} de {inicio} ate {fim}"
    
    @property
    def tipo_reserva_str(self):
        return TipoReservaEnum.TEMPORARIA

    def __repr__(self):
        return (
            f"Reservas_Fixas(id_reserva_temporaria={self.id_reserva_temporaria}, id_responsavel={self.id_responsavel}, "
            f"id_responsavel_especial={self.id_responsavel_especial}, tipo_responsavel={self.tipo_responsavel}, "
            f"id_reserva_local={self.id_reserva_local}, id_reserva_aula={self.id_reserva_aula}, "
            f"finalidade_reserva={self.finalidade_reserva}, observacoes={self.observacoes}, "
            f"descricao={self.descricao}, inicio_reserva={self.inicio_reserva}, "
            f"fim_reserva={self.fim_reserva})"
        )