
from sqlalchemy import (ForeignKey, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base

class Pessoas(Base):
    __tablename__ = 'pessoas'

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome_pessoa: Mapped[str] = mapped_column(String(100), nullable=False)
    email_pessoa: Mapped[str | None] = mapped_column(String(100))
    alias: Mapped[str | None] = mapped_column(String(100))

    reservas_fixas: Mapped[list["Reservas_Fixas"]] = relationship(back_populates='pessoa')
    reservas_temporarias: Mapped[list["Reservas_Temporarias"]] = relationship(back_populates='pessoa')
    usuarios: Mapped[list["Usuarios"]] = relationship(back_populates='pessoa')
    reservas_responsavel: Mapped[list["Reservas_Auditorios"]] = relationship(
        back_populates="responsavel",
        foreign_keys="Reservas_Auditorios.id_responsavel"
    )
    reservas_autorizador: Mapped[list["Reservas_Auditorios"]] = relationship(
        back_populates="autorizador",
        foreign_keys="Reservas_Auditorios.id_autorizador"
    )

    def __repr__(self) -> str:
        return (
            f"<Pessoas(id_pessoa={self.id_pessoa}, nome_pessoa={self.nome_pessoa}, "
            f"email_pessoa={self.email_pessoa})>"
        )
    
class Usuarios(Base):
    __tablename__ = 'usuarios'

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey('pessoas.id_pessoa'), nullable=False)
    tipo_pessoa: Mapped[str] = mapped_column(String(50), nullable=False)
    situacao_pessoa: Mapped[str] = mapped_column(String(50), nullable=False)
    grupo_pessoa: Mapped[str | None] = mapped_column(String(50))

    pessoa: Mapped["Pessoas"] = relationship(back_populates='usuarios')
    permissoes: Mapped[list["Permissoes"]] = relationship(back_populates='usuario')
    historicos: Mapped[list["Historicos"]] = relationship(back_populates='usuario')

    @property
    def username(self):
        return self.pessoa.nome_pessoa if self.pessoa else None
    
    @property
    def perm(self):
        return self.permissoes[0].permissao if self.permissoes else 0

    def __repr__(self) -> str:
        return (
            f"<Usuarios(id_usuario={self.id_usuario}, id_pessoa={self.id_pessoa}, "
            f"tipo_pessoa={self.tipo_pessoa}, situacao_pessoa={self.situacao_pessoa}, "
            f"grupo_pessoa={self.grupo_pessoa})>"
        )
    
    def __str__(self):
        uid = self.id_usuario
        pid = self.id_pessoa
        nome = self.pessoa.nome_pessoa
        return f"({uid}, {pid}) {nome}"
    
class Permissoes(Base):
    __tablename__ = 'permissoes'

    id_permissao_usuario: Mapped[int] = mapped_column(ForeignKey('usuarios.id_usuario'), primary_key=True)
    permissao: Mapped[int] = mapped_column(nullable=False)

    usuario: Mapped['Usuarios'] = relationship(back_populates='permissoes')

    def __repr__(self) -> str:
        return f"<Permissoes(id_permissao_usuario={self.id_permissao_usuario}, permissao={self.permissao})>"

class Usuarios_Especiais(Base):
    __tablename__ = 'usuarios_especiais'

    id_usuario_especial: Mapped[int] = mapped_column(primary_key=True)
    nome_usuario_especial: Mapped[str] = mapped_column(String(100), nullable=False)

    reservas_fixas: Mapped[list["Reservas_Fixas"]] = relationship(back_populates='usuario_especial')
    reservas_temporarias: Mapped[list["Reservas_Temporarias"]] = relationship(back_populates='usuario_especial')

    __table_args__ = (
        UniqueConstraint(
            'nome_usuario_especial',
            name='uq_usuario_especial'
        ),
    )

    def __repr__(self) -> str:
        return f"<Usuarios_Especiais(id_usuario_especial={self.id_usuario_especial}, nome_usuario_especial={self.nome_usuario_especial})>"
