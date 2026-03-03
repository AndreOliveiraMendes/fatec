from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auxiliar.model import parse_date
from app.enums import SituacaoChaveEnum, TipoMovimentacao, TipoReservaEnum
from app.extensions import Base

if TYPE_CHECKING:
    from app.models.aulas import Aulas_Ativas
    from app.models.locais import Locais

class Exibicao_Reservas(Base):
    __tablename__ = "exibicao_reservas"
    id_exibicao:Mapped[int] = mapped_column(primary_key=True)
    id_exibicao_local:Mapped[int] = mapped_column(ForeignKey("locais.id_local"), nullable=False)
    id_exibicao_aula:Mapped[int] = mapped_column(ForeignKey("aulas_ativas.id_aula_ativa"), nullable=False)
    exibicao_dia:Mapped[date] = mapped_column(nullable=False)

    tipo_reserva: Mapped[TipoReservaEnum] = mapped_column(
        Enum(TipoReservaEnum, name="tipo_reserva_enum", create_constraint=True),
        server_default=TipoReservaEnum.TEMPORARIA.name
    )

    __table_args__ = (
        UniqueConstraint(
            'id_exibicao_local',
            'id_exibicao_aula',
            'exibicao_dia',
            name="uq_exibicao_local_aula_dia"
        ),
    )

    local: Mapped["Locais"] = relationship(back_populates='exibicao_reservas')
    aula_ativa: Mapped["Aulas_Ativas"] = relationship(back_populates='exibicao_reservas')

    @property
    def selector_identification(self):
        aula = self.aula_ativa.selector_identification
        local = self.local.nome_local
        dia = parse_date(self.exibicao_dia)
        return f" {dia} no {local} as {aula}"

    def __repr__(self):
        return (
            f"Exibicao_Reservas(id_exibicao={self.id_exibicao}, id_exibicao_local={self.id_exibicao_local}, "
            f"id_exibicao_aula={self.id_exibicao_aula}, exibicao_dia={self.exibicao_dia}, "
            f"tipo_reserva={self.tipo_reserva})"
        )

class Situacoes_Das_Reserva(Base):
    __tablename__ = "situacoes_das_reservas"

    id_situacao:Mapped[int] = mapped_column(primary_key=True)
    id_situacao_local:Mapped[int] = mapped_column(ForeignKey("locais.id_local"), nullable=False)
    id_situacao_aula:Mapped[int] = mapped_column(ForeignKey("aulas_ativas.id_aula_ativa"), nullable=False)
    situacao_dia:Mapped[date] = mapped_column(nullable=False)

    situacao_chave: Mapped[SituacaoChaveEnum] = mapped_column(
        Enum(SituacaoChaveEnum, name="situacao_chave_enum", create_constraint=True),
        server_default=SituacaoChaveEnum.NAO_PEGOU_A_CHAVE.name
    )

    tipo_reserva: Mapped[TipoReservaEnum] = mapped_column(
        Enum(TipoReservaEnum, name="tipo_reserva_enum", create_constraint=True),
        server_default=TipoReservaEnum.FIXA.name
    )

    __table_args__ = (
        UniqueConstraint(
            'id_situacao_local',
            'id_situacao_aula',
            'situacao_dia',
            'tipo_reserva',
            name="uq_situacao_local_aula_dia_tipo"
        ),
    )

    local: Mapped["Locais"] = relationship(back_populates='situacoes_das_reservas')
    aula_ativa: Mapped["Aulas_Ativas"] = relationship(back_populates='situacoes_das_reservas')

    @property
    def selector_identification(self):
        aula = self.aula_ativa.selector_identification
        local = self.local.nome_local
        dia = parse_date(self.situacao_dia)
        return f" {dia} no {local} as {aula}"

    def __repr__(self) -> str:
        return (
            f"<SituacaoReserva(id_situacao={self.id_situacao}, id_situacao_local={self.id_situacao_local}, "
            f"id_situacao_aula={self.id_situacao_aula}, situacao_dia={self.situacao_dia} "
            f"situacao_chave={self.situacao_chave.value})>"
        )

class MovimentacaoEquipamento(Base):
    __tablename__ = "movimentacoes_equipamento"

    id_movimentacao: Mapped[int] = mapped_column(primary_key=True)
    id_equipamento: Mapped[int] = mapped_column(
        ForeignKey("equipamentos.id_equipamento"),
        nullable=False
    )
    tipo: Mapped[TipoMovimentacao] = mapped_column(
        Enum(TipoMovimentacao),
        nullable=False
    )
    quantidade: Mapped[int] = mapped_column(nullable=False)
    data_registro: Mapped[datetime] = mapped_column(
        default=datetime.now(),
        nullable=False
    )
    id_funcionario: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text)

class EquipamentoDisponibilidade(Base):
    __tablename__ = "equipamentos_disponibilidade"

    id_disponibilidade: Mapped[int] = mapped_column(primary_key=True)
    id_equipamento: Mapped[int] = mapped_column(
        ForeignKey("equipamentos.id_equipamento"),
        nullable=False
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    quantidade_disponivel: Mapped[int] = mapped_column(nullable=False)
    quantidade_reservada: Mapped[int] = mapped_column(nullable=False)
    gerado_em: Mapped[datetime] = mapped_column(
        default=datetime.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        default=datetime.now(),
        onupdate=datetime.now()
    )