import os
from pathlib import Path

semana_inglesa = {
    '%a': {  # abreviada
        'Mon': 'Seg', 'Tue': 'Ter', 'Wed': 'Qua', 'Thu': 'Qui',
        'Fri': 'Sex', 'Sat': 'Sáb', 'Sun': 'Dom'
    },
    '%A': {  # completa
        'Monday': 'segunda-feira', 'Tuesday': 'terça-feira', 'Wednesday': 'quarta-feira',
        'Thursday': 'quinta-feira', 'Friday': 'sexta-feira', 'Saturday': 'sábado', 'Sunday': 'domingo'
    }
}

meses_ingleses = {
    '%b': {  # abreviada
        'Jan': 'Jan', 'Feb': 'Fev', 'Mar': 'Mar', 'Apr': 'Abr',
        'May': 'Mai', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
        'Sep': 'Set', 'Oct': 'Out', 'Nov': 'Nov', 'Dec': 'Dez'
    },
    '%B': {  # completa
        'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
        'April': 'abril', 'May': 'maio', 'June': 'junho',
        'July': 'julho', 'August': 'agosto', 'September': 'setembro',
        'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
    }
}

mapa_icones_status = {
    None: ("text-muted", "glyphicon-user", None, "indefinido"),
    "NAO_PEGOU_A_CHAVE": ("text-danger", "glyphicon-user", "glyphicon-remove", "não pegou a chave"),
    "PEGOU_A_CHAVE": ("text-success", "glyphicon-user", "glyphicon-ok", "esta em sala"),
    "DEVOLVEU_A_CHAVE": ("text-primary", "glyphicon-user", "glyphicon-log-out", "reserva efetuada"),
}

situacoes_helper = [
    {
        "state":"exibicao",
        "url_path":'gestao_reserva.gerenciar_exibicao',
        "label": "controle de exibição"
    },{
        "state":"fixa",
        "url_path":'gestao_reserva.gerenciar_situacoes',
        "param":{
            "tipo_reserva":"fixa"
        },
        "label":"situação reserva fixa"
    },{
        "state":"temporaria",
        "url_path":'gestao_reserva.gerenciar_situacoes',
        "param":{
            "tipo_reserva":"temporaria"
        },
        "label":"situação reserva temporaria"
    },{
        "state":"comandos",
        "url_path":'gestao_reserva.comandos_remotos',
        "label":"comandos remotos"
    }
]

DEFAULT_PAINEL_CFG = {
    "tipo": "Aula",
    "tempo": "15",
    "laboratorios": "6"
}

DEFAULT_CONFIG_CFG = {
    "modo_gerenciacao": "multiplo",
    "toleranca": 20,
    "login": False
}

SECRET_PATH = "config/secret.json"

DATA_BASE = "data"
SSH_CRED_PATH = os.path.join("data", "ssh_credentials.json")
SSH_CRED_FILE = Path(SSH_CRED_PATH)
COMMANDS_PATH = os.path.join("data", "comandos.json")
COMMANDS_FILE = Path(COMMANDS_PATH)

ERRORS = {
    400: {"message": "Requisição inválida", "title": "Requisição inválida"},
    401: {"message": "Você precisa fazer login para acessar esta página.", "title": "Não autorizado"},
    403: {"message": "Você não possui as permissões necessárias para acessar esta página.", "title": "Acesso negado"},
    404: {"message": "A página requisitada não existe.", "title": "Página não encontrada"},
    409: {"message": "Conflito", "title": "Conflito"},
    422: {"message": "Entidade não processável.", "title": "Entidade não processável"},
    500: {"message": "Erro Interno do Servidor", "title": "Erro Interno do Servidor"}
}
