import os
from pathlib import Path

# --------------------------------------------------
# Form / request
# --------------------------------------------------

IGNORED_FORM_FIELDS = ['page', 'acao', 'bloco']


# --------------------------------------------------
# Datas (tradução EN → PT)
# --------------------------------------------------

semana_inglesa = {
    '%a': {  # abreviada
        'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui',
        'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'
    },
    '%A': {  # completa
        'Monday': 'segunda-feira',
        'Tuesday': 'terça-feira',
        'Wednesday': 'quarta-feira',
        'Thursday': 'quinta-feira',
        'Friday': 'sexta-feira',
        'Saturday': 'sábado',
        'Sunday': 'domingo'
    }
}

meses_ingleses = {
    '%b': {  # abreviada
        'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
        'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
        'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
    },
    '%B': {  # completa
        'January': 'janeiro',
        'February': 'fevereiro',
        'March': 'março',
        'April': 'abril',
        'May': 'maio',
        'June': 'junho',
        'July': 'julho',
        'August': 'agosto',
        'September': 'setembro',
        'October': 'outubro',
        'November': 'novembro',
        'December': 'dezembro'
    }
}


# --------------------------------------------------
# Status / UI
# --------------------------------------------------

mapa_icones_status = {
    None: ("text-default", "glyphicon-user", None, "indefinido"),
    "NAO_PEGOU_A_CHAVE": ("text-danger", "glyphicon-user", "glyphicon-remove", "não pegou a chave"),
    "PEGOU_A_CHAVE": ("text-success", "glyphicon-user", "glyphicon-ok", "esta em sala"),
    "DEVOLVEU_A_CHAVE": ("text-primary", "glyphicon-user", "glyphicon-log-out", "devolveu a chave"),
}

situacoes_helper = [
    {
        "key": "exibicao",
        "url_path": "exibicao_reserva.gerenciar_exibicao",
        "label": "controle de exibição",
        "enabled": True
    },
    {
        "key": "situacao",
        "url_path": "situacao_reservas.gerenciar_situacoes",
        "label": "situação reserva",
        "enabled": True
    },{
        "key":"fixa",
        "url_path":'gestao_reserva.gerenciar_situacoes',
        "param":{
            "tipo_reserva":"fixa"
        },
        "label":"situação reserva fixa",
        "enabled": False
    },{
        "key":"temporaria",
        "url_path":'gestao_reserva.gerenciar_situacoes',
        "param":{
            "tipo_reserva":"temporaria"
        },
        "label":"situação reserva temporaria",
        "enabled": False
    },{
        "key": "comandos",
        "url_path": "comandos_remotos.comandos_remotos",
        "label": "comandos remotos",
        "enabled": True
    },{
        "key": "equipamento",
        "url_path": "gestao_reserva_equipamento.gerenciar_reservas_equipamentos",
        "url_resume": "api.get_reservas_equipamentos",
        "target": "alertEquipamentos",
        "label": "reservas de equipamentos",
        "enabled": True
    }
]


# --------------------------------------------------
# Configuração padrão do painel
# --------------------------------------------------

DEFAULT_PAINEL_CFG = {
    "estilo1": {
        "tipo": "Aula",
        "tempo": "15",
        "laboratorios": "6",
        "status_indefinido": True,
        "modo_gerenciacao": "single"

    },
    "estilo2": {
        "tipo": "Aula",
        "tempo": "5",
        "laboratorios": "5",
        "status_indefinido": False,
        "modo_gerenciacao": "single"
    }
}

DEFAULT_CONFIG_CFG = {
    "modo_gerenciacao": "multiplo",
    "toleranca": 20,
    "navbar_redirect_target": "home",
    "login": False,
    "status_indefinido": True,
    "alertar": False,
    "tela_padrao": 1
}


# --------------------------------------------------
# Paths / arquivos
# --------------------------------------------------

SECRET_PATH = "config/secret.json"

DATA_BASE = "data"

SSH_CRED_PATH = os.path.join(DATA_BASE, "ssh_credentials.json")
SSH_CRED_FILE = Path(SSH_CRED_PATH)

COMMANDS_PATH = os.path.join(DATA_BASE, "comandos.json")
COMMANDS_FILE = Path(COMMANDS_PATH)


# --------------------------------------------------
# Erros HTTP
# --------------------------------------------------

ERRORS = {
    400: {"message": "Requisição inválida", "title": "Requisição inválida"},
    401: {"message": "Você precisa fazer login para acessar esta página.", "title": "Não autorizado"},
    403: {"message": "Você não possui as permissões necessárias para acessar esta página.", "title": "Acesso negado"},
    404: {"message": "A página requisitada não existe.", "title": "Página não encontrada"},
    409: {"message": "Conflito", "title": "Conflito"},
    422: {"message": "Entidade não processável.", "title": "Entidade não processável"},
    500: {"message": "Erro Interno do Servidor", "title": "Erro Interno do Servidor"}
}


# --------------------------------------------------
# Logs
# --------------------------------------------------

LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")


# --------------------------------------------------
# Limites
# --------------------------------------------------

MAX_RESULTS = 200