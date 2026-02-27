from datetime import date

from sqlalchemy import (TEXT, Enum, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import (StatusReservaAuditorioEnum)
from app.extensions import Base

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

    local: Mapped["Locais"] = relationship("Locais", back_populates="reservas_auditorios")
    aula_ativa: Mapped["Aulas_Ativas"] = relationship("Aulas_Ativas", back_populates="reservas_auditorios")
    responsavel: Mapped["Pessoas"] = relationship("Pessoas", back_populates="reservas_responsavel", foreign_keys=[id_responsavel])
    autorizador: Mapped["Pessoas"] = relationship("Pessoas", back_populates="reservas_autorizador", foreign_keys=[id_autorizador])

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