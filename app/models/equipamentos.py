from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base


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

class Categorias_de_Equipamentos(Base):
    __tablename__ = 'categorias_de_equipamentos'

    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    nome_categoria: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'nome_categoria',
            name="uq_nome_categoria"
        ),
    )

    equipamentos: Mapped[list["Equipamentos"]] = relationship(back_populates="categoria")