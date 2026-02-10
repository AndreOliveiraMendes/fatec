import enum


class SituacaoChaveEnum(enum.Enum):
    NAO_PEGOU_A_CHAVE = "não pegou a chave"
    PEGOU_A_CHAVE = "pegou a chave"
    DEVOLVEU_A_CHAVE = "devolveu a chave"

class TipoReservaEnum(enum.Enum):
    FIXA = "fixa"
    TEMPORARIA = "temporaria"

class FinalidadeReservaEnum(enum.Enum):
    GRADUACAO = "Graduação"
    ESPECIALIZACAO = "Especialização"
    EAD = "EAD"
    NAPTI = "NAPTI"
    CURSO = "Curso"
    USO_DOS_ALUNOS = "Uso dos Alunos"
    NEPLE = "NEPLE"

class DisponibilidadeEnum(enum.Enum):
    DISPONIVEL = "Disponivel"
    INDISPONIVEL = "Indisponivel"

class TipoLocalEnum(enum.Enum):
    LABORATORIO = "Laboratório"
    SALA = "Sala"
    EXTERNO = "Externo"
    AUDITORIO = "Auditorio"

class TipoAulaEnum(enum.Enum):
    AULA = "Aula"
    EVENTO = "Evento"
    OUTROS = "Outros"

class OrigemEnum(enum.Enum):
    SISTEMA = "Sistema"
    USUARIO = "Usuario"

class StatusReservaAuditorioEnum(enum.Enum):
    AGUARDANDO = "Aguardando"
    CANCELADA = "Cancelada"
    APROVADA = "Aprovada"
    REPROVADA = "Reprovada"