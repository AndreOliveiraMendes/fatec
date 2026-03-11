from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auxiliar.model import parse_date
from app.enums import SituacaoChaveEnum, TipoMovimentacaoEnum, TipoReservaEnum
from app.extensions import Base

if TYPE_CHECKING:
    from app.models.aulas import Aulas_Ativas
    from app.models.equipamentos import Equipamentos
    from app.models.locais import Locais
    from app.models.usuarios import Pessoas

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

    local: Mapped["Locais"] = relationship(back_populates='exibicao_reservas', passive_deletes=True)
    aula_ativa: Mapped["Aulas_Ativas"] = relationship(back_populates='exibicao_reservas', passive_deletes=True)

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

    local: Mapped["Locais"] = relationship(back_populates='situacoes_das_reservas', passive_deletes=True)
    aula_ativa: Mapped["Aulas_Ativas"] = relationship(back_populates='situacoes_das_reservas', passive_deletes=True)

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
    tipo: Mapped[TipoMovimentacaoEnum] = mapped_column(
        Enum(TipoMovimentacaoEnum),
        nullable=False
    )
    quantidade: Mapped[int] = mapped_column(nullable=False)
    data_registro: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False
    )
    id_funcionario: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    id_responsavel: Mapped[int | None] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text)

    equipamento: Mapped["Equipamentos"] = relationship(back_populates="movimentacoes", passive_deletes=True)
    funcionario: Mapped["Pessoas"] = relationship(back_populates="movimentacoes_funcionario", foreign_keys=[id_funcionario], passive_deletes=True)
    responsavel: Mapped["Pessoas"] = relationship(back_populates="movimentacoes_responsavel", foreign_keys=[id_responsavel], passive_deletes=True)

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

class EquipamentoDisponibilidade(Base):
    __tablename__ = "equipamentos_disponibilidade"

    id_disponibilidade: Mapped[int] = mapped_column(primary_key=True)
    id_equipamento: Mapped[int] = mapped_column(
        ForeignKey("equipamentos.id_equipamento"),
        nullable=False
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    quantidade_total: Mapped[int] = mapped_column(nullable=False)
    gerado_em: Mapped[datetime] = mapped_column(
        default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "id_equipamento",
            "data",
            name="uq_equipamento_data"
        ),
    )

    equipamento: Mapped["Equipamentos"] = relationship(back_populates="disponibilidades", passive_deletes=True)

    @property
    def selector_identification(self):
        equipamento = self.equipamento.nome_equipamento
        dia = parse_date(self.data)
        return f"{equipamento} no {dia}"
    
    def __repr__(self) -> str:
        return (
            f"<EquipamentoDisponibilidade("
            f"id_disponibilidade={self.id_disponibilidade}, "
            f"id_equipamento={self.id_equipamento}, "
            f"data={self.data}, "
            f"quantidade_disponivel={self.quantidade_disponivel}, "
            f"gerado_em={self.gerado_em}, "
            f"atualizado_em={self.atualizado_em}"
            f")>"
        )