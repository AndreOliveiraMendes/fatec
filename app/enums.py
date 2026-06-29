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

BASE = ["fixa", "temporaria"]

class TipoReservaExibicaoEnum(StrEnum):
    FIXA = BASE[0]
    TEMPORARIA = BASE[1]
    NENHUMA = "nenhuma"

class TipoReservaSituacaoEnum(StrEnum):
    FIXA = BASE[0]
    TEMPORARIA = BASE[1]

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

# ==============================
# Auditorios
# ==============================

class StatusReservaAuditorioEnum(StrEnum):
    AGUARDANDO = "Aguardando"
    APROVADA = "Aprovada"
    REPROVADA = "Reprovada"
    CANCELADA = "Cancelada"
    
class StatusEmailEnum(StrEnum):
    PENDENTE = "PENDENTE"
    ENVIANDO = "ENVIANDO"
    ENVIADO = "ENVIADO"
    ERRO = "ERRO"

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