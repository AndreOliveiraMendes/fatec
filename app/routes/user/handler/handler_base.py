from flask import url_for
from sqlalchemy import and_

from app.dao.internal.reservas import (check_periodo_auditorio,
                                       check_periodo_equipamento,
                                       check_periodo_fixa,
                                       check_periodo_temporaria,
                                       info_reserva_auditorio,
                                       info_reserva_equipamento,
                                       info_reserva_fixa,
                                       info_reserva_temporaria)
from app.enums import (StatusReservaAuditorioEnum,
                       StatusReservaEquipamentoEnum)
from app.models.aulas import Aulas_Ativas
from app.models.reservas.reservas_auditorios import Reservas_Auditorios
from app.models.reservas.reservas_equipamentos import Reservas_Equipamentos
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
    },
    "auditorio": {
        "model": Reservas_Auditorios,
        "order": Reservas_Auditorios.id_reserva_auditorio,
        "info": info_reserva_auditorio,
        "redirect": lambda: url_for('usuarios_reservas_auditorios.gerenciar_reservas_auditorios')
    },
    "equipamento": {
        "model": Reservas_Equipamentos,
        "order": Reservas_Equipamentos.id_reserva,
        "info": info_reserva_equipamento,
        "redirect": lambda: url_for('usuarios_reservas_equipamentos.gerenciar_reservas_equipamentos')
    }
}

FILTERS = {
    "fixa": {
        "semestre": (lambda s:Reservas_Fixas.id_reserva_semestre == s, int),
        "responsavel": (lambda r:Reservas_Fixas.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Fixas.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Fixas.id_reserva_local == l, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "finalidade": (lambda f:Reservas_Fixas.id_finalidade_reserva == f, str)
    },
    "temporaria": {
        "responsavel": (lambda r:Reservas_Temporarias.id_responsavel == r, int),
        "responsavel_especial": (lambda re:Reservas_Temporarias.id_responsavel_especial == re, int),
        "lab": (lambda l:Reservas_Temporarias.id_reserva_local == l, int),
        "dia": (lambda d:and_(Reservas_Temporarias.inicio_reserva <= d, Reservas_Temporarias.fim_reserva >= d), str),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "finalidade": (lambda f:Reservas_Temporarias.id_finalidade_reserva == f, str)
    },
    "auditorio": {
        "responsavel": (lambda r:Reservas_Auditorios.id_responsavel == r, int),
        "dia": (lambda d:Reservas_Auditorios.dia_reserva == d, str),
        "aud": (lambda a:Reservas_Auditorios.id_reserva_local == a, int),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "autorizador": (lambda a:Reservas_Auditorios.id_autorizador == a, int),
        "status": (lambda s:Reservas_Auditorios.status_reserva == StatusReservaAuditorioEnum(s), str)
    },
    "equipamento": {
        "responsavel": (lambda r:Reservas_Equipamentos.id_responsavel == r, int),
        "dia": (lambda d:Reservas_Equipamentos.data_reserva == d, str),
        "semana": (lambda s:Aulas_Ativas.id_semana == s, int),
        "status": (lambda s:Reservas_Equipamentos.status_reserva == StatusReservaEquipamentoEnum(s), str)
    }
}

CHECK_PERIODO_MAP = {
    Reservas_Fixas: lambda reserva: check_periodo_fixa(reserva),
    Reservas_Temporarias: lambda reserva: check_periodo_temporaria(reserva),
    Reservas_Auditorios: lambda reserva: check_periodo_auditorio(reserva),
    Reservas_Equipamentos: lambda reserva: check_periodo_equipamento(reserva)
}