
from sqlalchemy import TEXT, Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import DisponibilidadeEnum, TipoLocalEnum
from app.extensions import Base


class Locais(Base):
    __tablename__ = 'locais'

    id_local: Mapped[int] = mapped_column(primary_key=True)
    nome_local: Mapped[str] = mapped_column(String(100), nullable=False)
    descrição: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    disponibilidade: Mapped[DisponibilidadeEnum] = mapped_column(
        Enum(DisponibilidadeEnum, name="disponibilidade_enum", create_constraint=True),
        server_default=DisponibilidadeEnum.DISPONIVEL.name
    )

    tipo: Mapped[TipoLocalEnum] = mapped_column(
        Enum(TipoLocalEnum, name="tipo_local_enum", create_constraint=True),
        nullable=False,
        server_default=TipoLocalEnum.LABORATORIO.name
    )

    __table_args__ = (
        UniqueConstraint(
            'nome_local',
            name='uq_local'
        ),
    )

    reservas_fixas: Mapped[list["Reservas_Fixas"]] = relationship(back_populates='local')
    reservas_temporarias: Mapped[list["Reservas_Temporarias"]] = relationship(back_populates='local')
    reservas_auditorios: Mapped[list["Reservas_Auditorios"]] = relationship(back_populates='local')
    situacoes_das_reservas: Mapped[list["Situacoes_Das_Reserva"]] = relationship(back_populates='local') 
    exibicao_reservas: Mapped[list["Exibicao_Reservas"]] = relationship(back_populates='local')

    def __repr__(self) -> str:
        return (
            f"<Locais(id_local={self.id_local}, nome_local={self.nome_local}, "
            f"disponibilidade={self.disponibilidade.value}, tipo={self.tipo.value})>"
        )