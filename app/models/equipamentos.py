from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base

if TYPE_CHECKING:
    from app.models.controle import (EquipamentoDisponibilidade,
                                     MovimentacaoEquipamento)
    from app.models.reservas.reservas_equipamentos import \
        Reserva_Equipamento_Item

class Equipamentos(Base):
    __tablename__ = 'equipamentos'

    id_equipamento: Mapped[int] = mapped_column(primary_key=True)
    nome_equipamento: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    id_categoria: Mapped[int] = mapped_column(ForeignKey('categorias_de_equipamentos.id_categoria'), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'nome_equipamento',
            name="uq_nome_equipamento"
        ),
    )

    categoria: Mapped["Categorias_de_Equipamentos"] = relationship(back_populates="equipamentos")
    itens_reserva: Mapped[list["Reserva_Equipamento_Item"]] = relationship(
        back_populates="equipamento"
    )
    movimentacoes: Mapped[list["MovimentacaoEquipamento"]] = relationship(
        back_populates="equipamento"
    )
    disponibilidades: Mapped[list["EquipamentoDisponibilidade"]] = relationship(
        back_populates="equipamento"
    )

    def __repr__(self) -> str:
        return (
            f"<Equipamentos("
            f"id_equipamento={self.id_equipamento}, "
            f"nome_equipamento='{self.nome_equipamento}', "
            f"id_categoria={self.id_categoria}"
            f")>"
        )

class Categorias_de_Equipamentos(Base):
    __tablename__ = 'categorias_de_equipamentos'

    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    nome_categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            'nome_categoria',
            name="uq_nome_categoria"
        ),
    )

    equipamentos: Mapped[list["Equipamentos"]] = relationship(back_populates="categoria")

    def __repr__(self) -> str:
        return (
            f"<Categorias_de_Equipamentos("
            f"id_categoria={self.id_categoria}, "
            f"nome_categoria='{self.nome_categoria}'"
            f")>"
        )