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
    }
]

DEFAULT_PAINEL_CFG = {
    "tipo": "Aula",
    "tempo": "15",
    "laboratorios": "6"
}

DEFAULT_CONFIG_CFG = {
    "modo_gerenciacao": "multiplo",
    "toleranca": 20
}

SECRET_PATH = "config/secret.json"
SSH_CRED_PATH = "config/ssh_credentials.json"

ERROR_MESSAGES = {
    400: "Requisição inválida",
    401: "Você precisa fazer login para acessar esta página.",
    403: "Você não possui as permissões necessárias para acessar esta página.",
    404: "A página requisitada não existe.",
    409: "Conflito",
    422: "Entidade não processável.",
    500: "Erro Interno do Servidor"
}