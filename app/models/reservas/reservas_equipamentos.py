from datetime import datetime, date
from sqlalchemy import (
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import (
    Mapped, mapped_column
)
from app.extensions import Base

class Reservas_Equipamentos(Base):
    __tablename__ = "reservas_equipamentos"

    id_reserva: Mapped[int] = mapped_column(primary_key=True)
    id_reserva_aula: Mapped[int] = mapped_column(ForeignKey('aulas_ativas.id_aula_ativa'), nullable=False)
    id_reserva_responsavel: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'))
    data_reserva: Mapped[date] = mapped_column(nullable=False)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.now())

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

    __table_args__ = (
        UniqueConstraint(
            'id_reserva',
            'id_equipamento',
            name='uq_reserva_equipamento'
        ),
    )
