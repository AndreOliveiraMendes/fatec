from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base


class Configuracoes(Base):
    __tablename__ = "configuracoes"

    chave:Mapped[str] = mapped_column(String(100), primary_key=True)
    valor: Mapped[str] = mapped_column(String(255), nullable=False)