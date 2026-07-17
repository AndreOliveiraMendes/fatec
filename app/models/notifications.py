from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (DateTime, Enum, ForeignKey, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import StatusEmailEnum
from app.extensions import Base

if TYPE_CHECKING:
    from app.models.equipamentos import Equipamentos
    from app.models.reservas.reservas_auditorios import Reservas_Auditorios

class Reserva_Auditorio_Equipamentos(Base):
    __tablename__ = "reserva_auditorio_equipamentos"

    id_item: Mapped[int] = mapped_column(primary_key=True)
    id_reserva_auditorio: Mapped[int] = mapped_column(
        ForeignKey("reservas_auditorios.id_reserva_auditorio"),
        nullable=False
    )
    id_equipamento: Mapped[int] = mapped_column(
        ForeignKey("equipamentos.id_equipamento"),
        nullable=False
    )
    quantidade: Mapped[int] = mapped_column(nullable=False, server_default="1")
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            'id_reserva_auditorio',
            'id_equipamento',
            name='uq_reserva_auditorio_equipamento'
        ),
    )

    # relationships
    reserva_auditorio: Mapped["Reservas_Auditorios"] = relationship(
        "Reservas_Auditorios",
        back_populates="itens_equipamentos",
        passive_deletes=True
    )
    equipamento: Mapped["Equipamentos"] = relationship(
        "Equipamentos",
        back_populates="itens_reserva_auditorio",
        passive_deletes=True
    )

    @property
    def selector_identification(self) -> str:
        return f"Reserva {self.id_reserva_auditorio} ({self.reserva_auditorio.responsavel.nome_pessoa}) - Equipamento {self.id_equipamento} ({self.equipamento.nome_equipamento})"

    def __repr__(self) -> str:
        return (
            f"<ReservaAuditorioEquipamentos("
            f"id_reserva_auditorio={self.id_reserva_auditorio}, "
            f"id_equipamento={self.id_equipamento}, "
            f"quantidade={self.quantidade}, "
            f"observacoes={self.observacoes})>"
        )

class Reserva_Auditorio_Email(Base):
    __tablename__ = "reserva_auditorio_emails"

    id_email: Mapped[int] = mapped_column(primary_key=True)
    id_reserva_auditorio: Mapped[int] = mapped_column(
        ForeignKey("reservas_auditorios.id_reserva_auditorio"),
        nullable=False
    )
    destinatario: Mapped[str] = mapped_column(String(120), nullable=False)
    assunto: Mapped[str] = mapped_column(String(200), nullable=False)
    corpo_email: Mapped[str] = mapped_column(Text, nullable=False)
    status_envio: Mapped[StatusEmailEnum] = mapped_column(
        Enum(StatusEmailEnum, name="status_email_enum", create_constraint=True),
        nullable=False,
        server_default=StatusEmailEnum.PENDENTE.name
    )
    data_envio: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    erro_envio: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )
    tentativas: Mapped[int] = mapped_column(nullable=False, server_default="0")
    ultima_tentativa: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # relationship com reserva
    reserva_auditorio: Mapped["Reservas_Auditorios"] = relationship(
        "Reservas_Auditorios",
        back_populates="emails",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return (
            f"<Reserva_Auditorio_Email("
            f"id_email={self.id_email}, "
            f"id_reserva_auditorio={self.id_reserva_auditorio}, "
            f"status_envio={self.status_envio})>"
        )