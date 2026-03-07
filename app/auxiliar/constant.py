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
# Permission flags (bitmask)
# --------------------------------------------------

class Permission(IntFlag):
    RESERVA_FIXA = 1
    RESERVA_TEMPORARIA = 2
    RESERVA_AUDITORIO = 4
    ADMIN = 8
    AUTORIZAR = 16
    CMD_CONFIG = 32


PERMISSIONS = {
    "FIXA": Permission.RESERVA_FIXA,
    "TEMP": Permission.RESERVA_TEMPORARIA,
    "AUDITORIO": Permission.RESERVA_AUDITORIO,
    "ADMIN": Permission.ADMIN,
    "AUTORIZAR": Permission.AUTORIZAR,
    "CONFIGURAR_COMANDOS": Permission.CMD_CONFIG,
}


# --------------------------------------------------
# Date formatting flags (bitmask)
# --------------------------------------------------

DATA_NUMERICA = 0x1
DATA_ABREV = 0x2
DATA_COMPLETA = 0x4
HORA = 0x8
SEMANA_ABREV = 0x10
SEMANA_COMPLETA = 0x20


DATA_FLAGS = {
    "DATA_NUMERICA": DATA_NUMERICA,
    "DATA_ABREV": DATA_ABREV,
    "DATA_COMPLETA": DATA_COMPLETA,
    "HORA": HORA,
    "SEMANA_ABREV": SEMANA_ABREV,
    "SEMANA_COMPLETA": SEMANA_COMPLETA,
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