from enum import IntFlag

from sqlalchemy.exc import (DataError, IntegrityError, InterfaceError,
                            InternalError, OperationalError, ProgrammingError)

# --------------------------------------------------
# Database exceptions
# --------------------------------------------------

class IntervalConflictError(Exception):
    def __init__(self, message, table=None, fields=None, values=None, interval=None):
        self.message = message
        self.table = table
        self.fields = fields
        self.values = values
        self.interval = interval
        super().__init__(message)

    def __str__(self):
        context = []

        if self.table:
            context.append(f"table={self.table!r}")

        if self.fields:
            context.append(f"fields={self.fields!r}")

        if self.values:
            context.append(f"values={self.values!r}")
            
        if self.interval:
            context.append(f"interval={self.interval!r}")

        if context:
            return f"{self.message} | " + " ".join(context)

        return self.message

DB_ERRORS = (
    DataError,
    IntegrityError,
    InterfaceError,
    InternalError,
    OperationalError,
    ProgrammingError,
    IntervalConflictError
)

# --------------------------------------------------
# Schema exception
# --------------------------------------------------

class CircularDependencyError(Exception):
    pass

# --------------------------------------------------
# Permission flags (bitmask)
# --------------------------------------------------

class Permission(IntFlag):
    RESERVA_FIXA = 1
    RESERVA_TEMPORARIA = 2
    RESERVA_AUDITORIO = 4
    RESERVA_EQUIPAMENTO = 8
    ADMIN = 16
    AUTORIZAR = 32
    CMD_CONFIG = 64

    def has(self, perm):
        return (self & perm) == perm

    def has_any(self, perm):
        return bool(self & perm)

    def add(self, perm):
        return self | perm

    def remove(self, perm):
        return self & ~perm
    
    def list_permissions(self):
        return [perm for perm in Permission if self.has(perm)]
    
    @property
    def safe_name(self) -> str:
        return self.name or ""

    @property
    def description(self):
        return PERM_DESCRIPTIONS.get(self, "")

    @property
    def label(self):
        return PERM_LABELS.get(self, "")
    
PERM_DESCRIPTIONS = {
    Permission.RESERVA_FIXA: "Permissão de efetuar reservas fixas",
    Permission.RESERVA_TEMPORARIA: "Permissão de efetuar reservas temporárias",
    Permission.RESERVA_AUDITORIO: "Permissão de efetuar reservas de auditório",
    Permission.RESERVA_EQUIPAMENTO: "Permissão de efetuar reservas de equipamento",
    Permission.ADMIN: "Permissão de administração do sistema",
    Permission.AUTORIZAR: "Permissão de autorizar reservas de auditório",
    Permission.CMD_CONFIG: "Permissão de configurar comandos remotos",
}

PERM_LABELS = {
    Permission.RESERVA_FIXA: "Reserva Fixa",
    Permission.RESERVA_TEMPORARIA: "Reserva Temporária",
    Permission.RESERVA_AUDITORIO: "Reserva de Auditório",
    Permission.RESERVA_EQUIPAMENTO: "Reserva de Equipamento",
    Permission.ADMIN: "Administrador",
    Permission.AUTORIZAR: "Autorizador",
    Permission.CMD_CONFIG: "Configurador",
}

PERM_CRITICA = Permission.ADMIN | Permission.CMD_CONFIG

PERMISSIONS = {
    "FIXA": Permission.RESERVA_FIXA,
    "TEMP": Permission.RESERVA_TEMPORARIA,
    "AUDITORIO": Permission.RESERVA_AUDITORIO,
    "EQUIPAMENTO": Permission.RESERVA_EQUIPAMENTO,
    "ADMIN": Permission.ADMIN,
    "AUTORIZAR": Permission.AUTORIZAR,
    "CONFIGURAR_COMANDOS": Permission.CMD_CONFIG,
}


# --------------------------------------------------
# Date formatting flags (bitmask)
# --------------------------------------------------

class FormatDataTime(IntFlag):
    DATA_NUMERICA = 0x1
    DATA_ABREV = 0x2
    DATA_COMPLETA = 0x4
    HORA = 0x8
    SEMANA_ABREV = 0x10
    SEMANA_COMPLETA = 0x20

    def has(self, flag):
        return (self & flag) == flag

    def has_any(self, flag):
        return bool(self & flag)

DATA_FLAGS = {
    "DATA_NUMERICA": FormatDataTime.DATA_NUMERICA,
    "DATA_ABREV": FormatDataTime.DATA_ABREV,
    "DATA_COMPLETA": FormatDataTime.DATA_COMPLETA,
    "HORA": FormatDataTime.HORA,
    "SEMANA_ABREV": FormatDataTime.SEMANA_ABREV,
    "SEMANA_COMPLETA": FormatDataTime.SEMANA_COMPLETA,
}


# --------------------------------------------------
# Redirect targets
# --------------------------------------------------

REDIRECT_HOME = "home"
REDIRECT_TV = "tv"


# --------------------------------------------------
# App info
# --------------------------------------------------

APP_TITLE = "SGR"