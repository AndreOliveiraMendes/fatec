from flask import url_for
from sqlalchemy import and_

from app.dao.internal.reservas import (info_reserva_fixa,
                                       info_reserva_temporaria)
from app.enums import FinalidadeReservaEnum
from app.models.aulas import Aulas_Ativas
from app.models.reservas.reservas_laboratorios import (Reservas_Fixas,
                                                       Reservas_Temporarias)

RESERVA_MAP = {
    "fixa": {
        "model": Reservas_Fixas,
        "order": Reservas_Fixas.id_reserva_semestre,
        "info": info_reserva_fixa,
        "redirect": lambda: url_for('usuario_reservas_laboratorios.gerenciar_reserva_fixa')
    },
    "temporaria": {
        "model": Reservas_Temporarias,
        "order": Reservas_Temporarias.inicio_reserva,
        "info": info_reserva_temporaria,
        "redirect": lambda: url_for('usuario_reservas_laboratorios.gerenciar_reserva_temporaria')
    }
}

FILTERS = {
    "fixa": {
        "semestre": (lambda s:Reservas_Fixas.id_reserva_semestre == s, int),
        "responsavel": (lambda r:Reservas_Fixas.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Fixas.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Fixas.id_reserva_local == l, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "finalidade": (lambda f:Reservas_Fixas.finalidade_reserva == FinalidadeReservaEnum(f), str)
    },
    "temporaria": {
        "responsavel": (lambda r:Reservas_Temporarias.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Temporarias.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Temporarias.id_reserva_local == l, int),
        "dia": (lambda d:and_(Reservas_Temporarias.inicio_reserva <= d, Reservas_Temporarias.fim_reserva >= d), str),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "finalidade": (lambda f:Reservas_Temporarias.finalidade_reserva == FinalidadeReservaEnum(f), str)
    }
}