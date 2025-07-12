SECOES = {
    'Cadastro Básico': {
        'icon': 'glyphicon glyphicon-user',
        'secoes': [
            ('Pessoas', 'pessoas.gerenciar_pessoas', 'info', 'r'),
            ('Usuários', 'usuarios.gerenciar_usuarios', 'info', 'r'),
            ('Permissões', 'permissoes.gerenciar_permissoes', 'info', 'crud')
        ]
    },
    'Configurações': {
        'icon': 'glyphicon glyphicon-wrench',
        'secoes': [
            ('Usuários Especiais', 'usuarios_especiais.gerenciar_usuarios_especiais', 'success', 'crud'),
            ('Aulas', 'aulas.gerenciar_aulas', 'success', 'crud'),
            ('Laboratórios', 'laboratorios.gerenciar_laboratorios', 'success', 'crud'),
            ('Semestres', 'semestres.gerenciar_semestres', 'success', 'crud'),
            ('Dias da Semana', 'dias_da_semana.gerenciar_dias_da_semana', 'success', 'crud'),
            ('Turnos', 'turnos.gerenciar_turnos', 'success', 'crud')
        ]
    },
    'Operacional': {
        'icon': 'glyphicon glyphicon-calendar',
        'secoes': [
            ('Aulas Ativas', 'aulas_ativas.gerenciar_aulas_ativas', 'warning', 'crud'),
            ('Reservas Fixas', 'reservas_fixas.gerenciar_reservas_fixas', 'warning', 'crud'),
            ('Reservas Temporarias', 'reservas_temporarias.gerenciar_reservas_temporarias', 'warning', 'crud')
        ]
    },
    'Logs / Histórico': {
        'icon': 'glyphicon glyphicon-list-alt',
        'secoes': [
            ('Histórico', 'historicos.gerenciar_Historicos', 'danger', 're')
        ]
    }
}
TABLES_PER_LINE = 10