from enum import IntEnum, StrEnum

# ==============================
# Fluxo / Sistema
# ==============================

class ActionEnum(StrEnum):
    ABERTURA = "abertura"
    LISTAR = "listar"
    PROCURAR = "procurar"
    INSERIR = "inserir"
    EDITAR = "editar"
    EXCLUIR = "excluir"
    EXPORTAR = "exportar"

class StepEnum(IntEnum):
    S0 = 0
    S1 = 1
    S2 = 2

class StatusEnum(StrEnum):
    DISABLED = "disabled"
    ENABLED = "enabled"
#    EXTRA = "extra"

class OrigemEnum(StrEnum):
    SISTEMA = "Sistema"
    USUARIO = "Usuario"

# ==============================
# Reservas
# ==============================

class TipoReservaEnum(StrEnum):
    FIXA = "fixa"
    TEMPORARIA = "temporaria"

class TipoAulaEnum(StrEnum):
    AULA = "Aula"
    EVENTO = "Evento"
    OUTROS = "Outros"

# ==============================
# Locais
# ==============================

class TipoLocalEnum(StrEnum):
    LABORATORIO = "Laboratório"
    SALA = "Sala"
    EXTERNO = "Externo"
    AUDITORIO = "Auditorio"

class DisponibilidadeEnum(StrEnum):
    DISPONIVEL = "Disponivel"
    INDISPONIVEL = "Indisponivel"

# ==============================
# Auditorios
# ==============================

class StatusReservaAuditorioEnum(StrEnum):
    AGUARDANDO = "Aguardando"
    APROVADA = "Aprovada"
    REPROVADA = "Reprovada"
    CANCELADA = "Cancelada"

# ==============================
# Equipamentos
# ==============================

class StatusReservaEquipamentoEnum(StrEnum):
    PENDENTE = "pendente"
    ATIVA = "ativa"
    CANCELADA = "cancelada"
    CONCLUIDA = "concluida"

class TipoMovimentacaoEnum(StrEnum):
    EMPRESTIMO = "emprestimo"
    DEVOLUCAO = "devolucao"
    REPOSICAO = "reposicao"
    MANUTENCAO = "manutencao"
    AJUSTE = "ajuste"

# ==============================
# Chaves
# ==============================

class SituacaoChaveEnum(StrEnum):
    NAO_PEGOU_A_CHAVE = "não pegou a chave"
    PEGOU_A_CHAVE = "pegou a chave"
    DEVOLVEU_A_CHAVE = "devolveu a chave"