from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TEXT, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import OrigemEnum
from app.extensions import Base

if TYPE_CHECKING:
    from app.models.usuarios import Usuarios

class Historicos(Base):
    __tablename__ = 'historicos'

    id_historico: Mapped[int] = mapped_column(primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey('usuarios.id_usuario'), nullable=True)
    tabela: Mapped[str | None] = mapped_column(String(100), index=True)
    categoria: Mapped[str | None] = mapped_column(String(100))
    data_hora: Mapped[datetime] = mapped_column(index=True, nullable=False)
    message: Mapped[str] = mapped_column(TEXT, nullable=False)
    chave_primaria: Mapped[str] = mapped_column(TEXT, nullable=False)
    observacao: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    origem: Mapped[OrigemEnum] = mapped_column(
        Enum(OrigemEnum, name="origem_enum", create_constraint=True),
        server_default=OrigemEnum.SISTEMA.name
    )

    usuario: Mapped["Usuarios"] = relationship(back_populates='historicos')

    def __repr__(self) -> str:
        return (
            f"<Historicos(id_historico={self.id_historico}, id_usuario={self.id_usuario}, "
            f"tabela={self.tabela}, categoria={self.categoria}, "
            f"data_hora={self.data_hora}, message={self.message}, "
            f"chave_primaria={self.chave_primaria}, observacao={self.observacao})>"
        )

