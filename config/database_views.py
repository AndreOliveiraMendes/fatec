from typing import NamedTuple, TypedDict


class Secao(NamedTuple):
    nome: str
    endpoint: str
    cor: str
    meta: str

class SecaoGrupo(TypedDict):
    icon: str
    secoes: list[Secao]

SECOES: dict[str, SecaoGrupo]
SECOES: dict[str, SecaoGrupo] = {
    'Cadastro Básico': {
        'icon': 'glyphicon glyphicon-user',
        'secoes': [
            Secao('Pessoas', 'database_pessoas.gerenciar_pessoas', 'info', 'ru'),
            Secao('Usuários', 'database_usuarios.gerenciar_usuarios', 'info', 'r'),
            Secao('Permissões', 'database_permissoes.gerenciar_permissoes', 'info', 'crud')
        ]
    },
    'Configurações': {
        'icon': 'glyphicon glyphicon-wrench',
        'secoes': [
            Secao('Usuários Especiais', 'database_usuarios_especiais.gerenciar_usuarios_especiais', 'success', 'crud'),
            Secao('Aulas', 'database_aulas.gerenciar_aulas', 'success', 'crud'),
            Secao('Locais', 'database_locais.gerenciar_locais', 'success', 'crud'),
            Secao('Equipamento', 'database_equipamentos.gerenciar_equipamentos', 'success', 'crud'),
            Secao('Semestres', 'database_semestres.gerenciar_semestres', 'success', 'crud'),
            Secao('Dias da Semana', 'database_dias_da_semana.gerenciar_dias_da_semana', 'success', 'crud'),
            Secao('Turnos', 'database_turnos.gerenciar_turnos', 'success', 'crud'),
            Secao('Categoria de Equipamento', 'database_categorias_de_equipamentos.gerenciar_categorias_de_equipamentos', 'success', 'crud')
        ]
    },
    'Operacional': {
        'icon': 'glyphicon glyphicon-calendar',
        'secoes': [
            Secao('Aulas Ativas', 'database_aulas_ativas.gerenciar_aulas_ativas', 'warning', 'crud'),
            Secao('Reservas Fixas', 'database_reservas_fixas.gerenciar_reservas_fixas', 'warning', 'crud'),
            Secao('Reservas Temporarias', 'database_reservas_temporarias.gerenciar_reservas_temporarias', 'warning', 'crud'),
            Secao('Reserva Auditorio', 'database_reservas_auditorios.gerenciar_reservas_auditorios', 'warning', 'crud'),
            Secao('Reserva Equipamento', 'default.under_dev_page', 'warning', 'crud')
        ]
    },
    'Operacional / Configuração':{
        'icon': 'glyphicon glyphicon-cog',
        'secoes': [
            Secao('Situacoes das reservas', 'database_situacoes_das_reservas.gerenciar_situacoes_das_reservas', 'warning', 'crud'),
            Secao('Exibicao das reservas', 'database_exibicao_reservas.gerenciar_exibicao_reservas', 'warning', 'crud'),
            Secao('Item da reserva de equipamento', 'default.under_dev_page', 'warning', 'crud')
        ]
    },
    'Logs / Histórico': {
        'icon': 'glyphicon glyphicon-list-alt',
        'secoes': [
            Secao('Histórico', 'database_historicos.gerenciar_historicos', 'danger', 're'),
            Secao('Movimentação equipamento', 'default.under_dev_page', 'danger', 'crud'),
            Secao('Quantidade Equipamento', 'default.under_dev_page', 'danger', 'crud')
        ]
    }
}
SETUP_HEAD = [
    {
        "url": "setup.fast_setup_menu",
        "label": "Setup Rapido",
        "icon": "glyphicon-flash",
        "category":"danger"
    }
]
URL_INDEX = {
    s.endpoint.split('.', 1)[0]: s.endpoint
    for secao in SECOES.values()
    for s in secao["secoes"]
}
def get_url(blueprint_name):
    return URL_INDEX.get(blueprint_name, 'default.under_dev_page')