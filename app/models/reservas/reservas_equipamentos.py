from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import StatusReservaEquipamentoEnum
from app.extensions import Base

if TYPE_CHECKING:
    from app.models.aulas import Aulas_Ativas
    from app.models.equipamentos import Equipamentos
    from app.models.usuarios import Pessoas

class Reservas_Equipamentos(Base):
    __tablename__ = "reservas_equipamentos"

    id_reserva: Mapped[int] = mapped_column(primary_key=True)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    id_reserva_responsavel: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'))
    data_reserva: Mapped[date] = mapped_column(nullable=False)
    criado_em: Mapped[datetime] = mapped_column(default=func.now())
    cancelado_em: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelado_por_id: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    estado: Mapped[StatusReservaEquipamentoEnum] = mapped_column(
        Enum(StatusReservaEquipamentoEnum),
        server_default=StatusReservaEquipamentoEnum.PENDENTE.name,
        nullable=False
    )

    aula_ativa: Mapped["Aulas_Ativas"] = relationship(back_populates="reservas_equipamentos", passive_deletes=True)
    responsavel: Mapped["Pessoas"] = relationship(back_populates="reservas_equipamentos", foreign_keys=[id_reserva_responsavel], passive_deletes=True)
    cancelado_por: Mapped["Pessoas"] = relationship(foreign_keys=[cancelado_por_id], back_populates="reservas_canceladas", passive_deletes=True)
    itens: Mapped[list["Reserva_Equipamento_Item"]] = relationship(back_populates="reserva", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"<Reservas_Equipamentos("
            f"id_reserva={self.id_reserva}, "
            f"id_reserva_aula={self.id_reserva_aula}, "
            f"id_reserva_responsavel={self.id_reserva_responsavel}, "
            f"data_reserva={self.data_reserva}"
            f"criado_em={self.criado_em}"
            f")>"
        )

class Reserva_Equipamento_Item(Base):
    __tablename__ = "reservas_equipamentos_items"

    id_item: Mapped[int] = mapped_column(primary_key=True)
    id_reserva: Mapped[int] = mapped_column(
        ForeignKey("reservas_equipamentos.id_reserva"), nullable=False
    )
    id_equipamento: Mapped[int] = mapped_column(
        ForeignKey("equipamentos.id_equipamento"), nullable=False
    )
    quantidade: Mapped[int] = mapped_column(nullable=False, default=1)
    devolvido: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            'id_reserva',
            'id_equipamento',
            name='uq_reserva_equipamento'
        ),
    )

    reserva: Mapped["Reservas_Equipamentos"] = relationship(back_populates="itens", passive_deletes=True)
    equipamento: Mapped["Equipamentos"] = relationship(back_populates="itens_reserva", passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"<Reserva_Equipamento_Item("
            f"id_item={self.id_item}, "
            f"id_reserva={self.id_reserva}, "
            f"id_equipamento={self.id_equipamento}, "
            f"quantidade={self.quantidade}"
            f")>"
        )