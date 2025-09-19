SECOES = {
    'Cadastro Básico': {
        'icon': 'glyphicon glyphicon-user',
        'secoes': [
            ('Pessoas', 'database_pessoas.gerenciar_pessoas', 'info', 'ru'),
            ('Usuários', 'database_usuarios.gerenciar_usuarios', 'info', 'r'),
            ('Permissões', 'database_permissoes.gerenciar_permissoes', 'info', 'crud')
        ]
    },
    'Configurações': {
        'icon': 'glyphicon glyphicon-wrench',
        'secoes': [
            ('Usuários Especiais', 'database_usuarios_especiais.gerenciar_usuarios_especiais', 'success', 'crud'),
            ('Aulas', 'database_aulas.gerenciar_aulas', 'success', 'crud'),
            ('Locais', 'database_locais.gerenciar_locais', 'success', 'crud'),
            ('Semestres', 'database_semestres.gerenciar_semestres', 'success', 'crud'),
            ('Dias da Semana', 'database_dias_da_semana.gerenciar_dias_da_semana', 'success', 'crud'),
            ('Turnos', 'database_turnos.gerenciar_turnos', 'success', 'crud')
        ]
    },
    'Operacional': {
        'icon': 'glyphicon glyphicon-calendar',
        'secoes': [
            ('Aulas Ativas', 'database_aulas_ativas.gerenciar_aulas_ativas', 'warning', 'crud'),
            ('Reservas Fixas', 'database_reservas_fixas.gerenciar_reservas_fixas', 'warning', 'crud'),
            ('Reservas Temporarias', 'database_reservas_temporarias.gerenciar_reservas_temporarias', 'warning', 'crud'),
            ('Reserva Auditorio', 'database_reservas_auditorios.gerenciar_reservas_auditorios', 'warning', 'crud')
        ]
    },
    'Operacional / Configuração':{
        'icon': 'glyphicon glyphicon-cog',
        'secoes': [
            ('Situacoes das reservas', 'database_situacoes_das_reservas.gerenciar_situacoes_das_reservas', 'warning', 'crud'),
            ('Exibicao das reservas', 'database_exibicao_reservas.gerenciar_exibicao_reservas', 'warning', 'crud')
        ]
    },
    'Logs / Histórico': {
        'icon': 'glyphicon glyphicon-list-alt',
        'secoes': [
            ('Histórico', 'database_historicos.gerenciar_historicos', 'danger', 're')
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