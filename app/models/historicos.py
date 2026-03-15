from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import TEXT, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auxiliar.model import parse_datetime
from app.enums import OrigemEnum, TipoMovimentacaoEnum
from app.extensions import Base

if TYPE_CHECKING:
    from app.models.equipamentos import Equipamentos
    from app.models.usuarios import Pessoas, Usuarios

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

    usuario: Mapped["Usuarios"] = relationship(back_populates='historicos', passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"<Historicos(id_historico={self.id_historico}, id_usuario={self.id_usuario}, "
            f"tabela={self.tabela}, categoria={self.categoria}, "
            f"data_hora={self.data_hora}, message={self.message}, "
            f"chave_primaria={self.chave_primaria}, observacao={self.observacao})>"
        )

class MovimentacaoEquipamento(Base):
    __tablename__ = "movimentacoes_equipamento"

    id_movimentacao: Mapped[int] = mapped_column(primary_key=True)
    id_equipamento: Mapped[int] = mapped_column(
        ForeignKey("equipamentos.id_equipamento"),
        nullable=False
    )
    tipo: Mapped[TipoMovimentacaoEnum] = mapped_column(
        Enum(TipoMovimentacaoEnum),
        nullable=False
    )
    quantidade: Mapped[int] = mapped_column(nullable=False)
    data_registro: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    id_funcionario: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text)

    equipamento: Mapped["Equipamentos"] = relationship(back_populates="movimentacoes", passive_deletes=True)
    funcionario: Mapped["Pessoas"] = relationship(back_populates="movimentacoes_funcionario", foreign_keys=[id_funcionario], passive_deletes=True)
    responsavel: Mapped["Pessoas"] = relationship(back_populates="movimentacoes_responsavel", foreign_keys=[id_responsavel], passive_deletes=True)

    @property
    def selector_identification(self):
        equipamento = self.equipamento.nome_equipamento
        dia = parse_datetime(self.data_registro)
        return f"{equipamento}, {dia}"

    def __repr__(self) -> str:
        return (
            f"<MovimentacaoEquipamento("
            f"id_movimentacao={self.id_movimentacao}, "
            f"id_equipamento={self.id_equipamento}, "
            f"tipo={self.tipo}, "
            f"quantidade={self.quantidade}, "
            f"id_funcionario={self.id_funcionario}, "
            f"id_responsavel={self.id_responsavel}, "
            f"data_registro={self.data_registro}"
            f")>"
        )