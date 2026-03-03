CREATE TABLE
    IF NOT EXISTS aulas (
        id_aula INTEGER NOT NULL AUTO_INCREMENT,
        horario_inicio TIME NOT NULL,
        horario_fim TIME NOT NULL,
        PRIMARY KEY (id_aula),
        CONSTRAINT uq_aula_inicio_fim UNIQUE (horario_inicio, horario_fim)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS categorias_de_equipamentos (
        id_categoria INTEGER NOT NULL AUTO_INCREMENT,
        nome_categoria VARCHAR(100) NOT NULL,
        PRIMARY KEY (id_categoria),
        CONSTRAINT uq_nome_categoria UNIQUE (nome_categoria)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS dias_da_semana (
        id_semana INTEGER NOT NULL,
        nome_semana VARCHAR(15) NOT NULL,
        PRIMARY KEY (id_semana),
        CONSTRAINT nome_semana UNIQUE (nome_semana)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS locais (
        id_local INTEGER NOT NULL AUTO_INCREMENT,
        nome_local VARCHAR(100) NOT NULL,
        `descrição` TEXT,
        disponibilidade ENUM ('DISPONIVEL', 'INDISPONIVEL') NOT NULL DEFAULT 'DISPONIVEL',
        tipo ENUM ('LABORATORIO', 'SALA', 'EXTERNO', 'AUDITORIO') NOT NULL DEFAULT 'LABORATORIO',
        PRIMARY KEY (id_local),
        CONSTRAINT uq_local UNIQUE (nome_local)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS pessoas (
        id_pessoa INTEGER NOT NULL AUTO_INCREMENT,
        nome_pessoa VARCHAR(100) NOT NULL,
        email_pessoa VARCHAR(100),
        alias VARCHAR(100),
        PRIMARY KEY (id_pessoa)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS semestres (
        id_semestre INTEGER NOT NULL AUTO_INCREMENT,
        nome_semestre VARCHAR(100) NOT NULL,
        data_inicio DATE NOT NULL,
        data_fim DATE NOT NULL,
        data_inicio_reserva DATE NOT NULL,
        data_fim_reserva DATE NOT NULL,
        dias_de_prioridade INTEGER NOT NULL,
        PRIMARY KEY (id_semestre),
        CONSTRAINT uq_semestre_inicio_fim UNIQUE (data_inicio, data_fim),
        CONSTRAINT uq_semestre_inicio_fim_reserva UNIQUE (data_inicio_reserva, data_fim_reserva),
        CONSTRAINT uq_semestre_nome UNIQUE (nome_semestre)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS turnos (
        id_turno INTEGER NOT NULL AUTO_INCREMENT,
        nome_turno VARCHAR(50) NOT NULL,
        horario_inicio TIME NOT NULL,
        horario_fim TIME NOT NULL,
        PRIMARY KEY (id_turno),
        CONSTRAINT nome_turno UNIQUE (nome_turno),
        CONSTRAINT uq_turno_inicio_fim UNIQUE (horario_inicio, horario_fim)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS usuarios_especiais (
        id_usuario_especial INTEGER NOT NULL AUTO_INCREMENT,
        nome_usuario_especial VARCHAR(100) NOT NULL,
        PRIMARY KEY (id_usuario_especial),
        CONSTRAINT uq_usuario_especial UNIQUE (nome_usuario_especial)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS aulas_ativas (
        id_aula_ativa INTEGER NOT NULL AUTO_INCREMENT,
        id_aula INTEGER NOT NULL,
        inicio_ativacao DATE,
        fim_ativacao DATE,
        id_semana INTEGER NOT NULL,
        tipo_aula ENUM ('AULA', 'EVENTO', 'OUTROS') NOT NULL DEFAULT 'AULA',
        PRIMARY KEY (id_aula_ativa),
        CONSTRAINT aulas_ativas_ibfk_1 FOREIGN KEY (id_aula) REFERENCES aulas (id_aula),
        CONSTRAINT aulas_ativas_ibfk_2 FOREIGN KEY (id_semana) REFERENCES dias_da_semana (id_semana),
        CONSTRAINT chk_aula_ativa_inicio_menor_fim CHECK (
            (
                (`inicio_ativacao` is null)
                or (`fim_ativacao` is null)
                or (`inicio_ativacao` <= `fim_ativacao`)
            )
        )
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS equipamentos (
        id_equipamento INTEGER NOT NULL AUTO_INCREMENT,
        nome_equipamento VARCHAR(120) NOT NULL,
        descricao TEXT,
        id_categoria INTEGER NOT NULL,
        PRIMARY KEY (id_equipamento),
        CONSTRAINT equipamentos_ibfk_1 FOREIGN KEY (id_categoria) REFERENCES categorias_de_equipamentos (id_categoria),
        CONSTRAINT uq_nome_equipamento UNIQUE (nome_equipamento)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS usuarios (
        id_usuario INTEGER NOT NULL AUTO_INCREMENT,
        id_pessoa INTEGER NOT NULL,
        tipo_pessoa VARCHAR(50) NOT NULL,
        situacao_pessoa VARCHAR(50) NOT NULL,
        grupo_pessoa VARCHAR(50),
        PRIMARY KEY (id_usuario),
        CONSTRAINT usuarios_ibfk_1 FOREIGN KEY (id_pessoa) REFERENCES pessoas (id_pessoa)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS equipamentos_disponibilidade (
        id_disponibilidade INTEGER NOT NULL AUTO_INCREMENT,
        id_equipamento INTEGER NOT NULL,
        data DATE NOT NULL,
        quantidade_disponivel INTEGER NOT NULL,
        quantidade_reservada INTEGER NOT NULL,
        gerado_em DATETIME NOT NULL,
        atualizado_em DATETIME NOT NULL,
        PRIMARY KEY (id_disponibilidade),
        CONSTRAINT equipamentos_disponibilidade_ibfk_1 FOREIGN KEY (id_equipamento) REFERENCES equipamentos (id_equipamento)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS exibicao_reservas (
        id_exibicao INTEGER NOT NULL AUTO_INCREMENT,
        id_exibicao_local INTEGER NOT NULL,
        id_exibicao_aula INTEGER NOT NULL,
        exibicao_dia DATE NOT NULL,
        tipo_reserva ENUM ('FIXA', 'TEMPORARIA') NOT NULL DEFAULT 'TEMPORARIA',
        PRIMARY KEY (id_exibicao),
        CONSTRAINT exibicao_reservas_ibfk_1 FOREIGN KEY (id_exibicao_local) REFERENCES locais (id_local),
        CONSTRAINT exibicao_reservas_ibfk_2 FOREIGN KEY (id_exibicao_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT uq_exibicao_local_aula_dia UNIQUE (id_exibicao_local, id_exibicao_aula, exibicao_dia)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS historicos (
        id_historico INTEGER NOT NULL AUTO_INCREMENT,
        id_usuario INTEGER,
        tabela VARCHAR(100),
        categoria VARCHAR(100),
        data_hora DATETIME NOT NULL,
        message TEXT NOT NULL,
        chave_primaria TEXT NOT NULL,
        observacao TEXT,
        origem ENUM ('SISTEMA', 'USUARIO') NOT NULL DEFAULT 'SISTEMA',
        PRIMARY KEY (id_historico),
        CONSTRAINT historicos_ibfk_1 FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS movimentacoes_equipamento (
        id_movimentacao INTEGER NOT NULL AUTO_INCREMENT,
        id_equipamento INTEGER NOT NULL,
        tipo ENUM (
            'Inicial',
            'EMPRESTIMO',
            'DEVOLUCAO',
            'REPOSICAO',
            'AJUSTE'
        ) NOT NULL,
        quantidade INTEGER NOT NULL,
        data_registro DATETIME NOT NULL,
        id_funcionario INTEGER NOT NULL,
        id_responsavel INTEGER,
        observacao TEXT,
        PRIMARY KEY (id_movimentacao),
        CONSTRAINT movimentacoes_equipamento_ibfk_1 FOREIGN KEY (id_equipamento) REFERENCES equipamentos (id_equipamento),
        CONSTRAINT movimentacoes_equipamento_ibfk_2 FOREIGN KEY (id_funcionario) REFERENCES pessoas (id_pessoa),
        CONSTRAINT movimentacoes_equipamento_ibfk_3 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS permissoes (
        id_permissao_usuario INTEGER NOT NULL,
        permissao INTEGER NOT NULL,
        PRIMARY KEY (id_permissao_usuario),
        CONSTRAINT permissoes_ibfk_1 FOREIGN KEY (id_permissao_usuario) REFERENCES usuarios (id_usuario)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS reservas_auditorios (
        id_reserva_auditorio INTEGER NOT NULL AUTO_INCREMENT,
        id_responsavel INTEGER NOT NULL,
        id_reserva_local INTEGER NOT NULL,
        id_reserva_aula INTEGER NOT NULL,
        dia_reserva DATE NOT NULL,
        status_reserva ENUM (
            'AGUARDANDO',
            'CANCELADA',
            'APROVADA',
            'REPROVADA'
        ) NOT NULL DEFAULT 'AGUARDANDO',
        id_autorizador INTEGER,
        `observação_responsavel` TEXT,
        `observação_autorizador` TEXT,
        PRIMARY KEY (id_reserva_auditorio),
        CONSTRAINT reservas_auditorios_ibfk_1 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa),
        CONSTRAINT reservas_auditorios_ibfk_2 FOREIGN KEY (id_reserva_local) REFERENCES locais (id_local),
        CONSTRAINT reservas_auditorios_ibfk_3 FOREIGN KEY (id_reserva_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT reservas_auditorios_ibfk_4 FOREIGN KEY (id_autorizador) REFERENCES pessoas (id_pessoa),
        CONSTRAINT uq_reserva_responsavel_local_aula_dia UNIQUE (
            id_responsavel,
            id_reserva_local,
            id_reserva_aula,
            dia_reserva
        )
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS reservas_equipamentos (
        id_reserva INTEGER NOT NULL AUTO_INCREMENT,
        id_reserva_aula INTEGER NOT NULL,
        id_reserva_responsavel INTEGER NOT NULL,
        data_reserva DATE NOT NULL,
        criado_em DATETIME NOT NULL,
        PRIMARY KEY (id_reserva),
        CONSTRAINT reservas_equipamentos_ibfk_1 FOREIGN KEY (id_reserva_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT reservas_equipamentos_ibfk_2 FOREIGN KEY (id_reserva_responsavel) REFERENCES pessoas (id_pessoa)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS reservas_fixas (
        id_reserva_fixa INTEGER NOT NULL AUTO_INCREMENT,
        id_reserva_semestre INTEGER NOT NULL,
        id_responsavel INTEGER,
        id_responsavel_especial INTEGER,
        id_reserva_local INTEGER NOT NULL,
        id_reserva_aula INTEGER NOT NULL,
        finalidade_reserva ENUM (
            'GRADUACAO',
            'ESPECIALIZACAO',
            'EAD',
            'NAPTI',
            'CURSO',
            'USO_DOS_ALUNOS',
            'NEPLE'
        ) NOT NULL DEFAULT 'GRADUACAO',
        observacoes TEXT,
        descricao VARCHAR(100),
        PRIMARY KEY (id_reserva_fixa),
        CONSTRAINT reservas_fixas_ibfk_1 FOREIGN KEY (id_reserva_semestre) REFERENCES semestres (id_semestre),
        CONSTRAINT reservas_fixas_ibfk_2 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa),
        CONSTRAINT reservas_fixas_ibfk_3 FOREIGN KEY (id_responsavel_especial) REFERENCES usuarios_especiais (id_usuario_especial),
        CONSTRAINT reservas_fixas_ibfk_4 FOREIGN KEY (id_reserva_local) REFERENCES locais (id_local),
        CONSTRAINT reservas_fixas_ibfk_5 FOREIGN KEY (id_reserva_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT uq_reserva_local_aula_semestre UNIQUE (
            id_reserva_local,
            id_reserva_aula,
            id_reserva_semestre
        )
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS reservas_temporarias (
        id_reserva_temporaria INTEGER NOT NULL AUTO_INCREMENT,
        inicio_reserva DATE NOT NULL,
        fim_reserva DATE NOT NULL,
        id_responsavel INTEGER,
        id_responsavel_especial INTEGER,
        id_reserva_local INTEGER NOT NULL,
        id_reserva_aula INTEGER NOT NULL,
        finalidade_reserva ENUM (
            'GRADUACAO',
            'ESPECIALIZACAO',
            'EAD',
            'NAPTI',
            'CURSO',
            'USO_DOS_ALUNOS',
            'NEPLE'
        ) NOT NULL DEFAULT 'GRADUACAO',
        observacoes TEXT,
        descricao VARCHAR(100),
        PRIMARY KEY (id_reserva_temporaria),
        CONSTRAINT reservas_temporarias_ibfk_1 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa),
        CONSTRAINT reservas_temporarias_ibfk_2 FOREIGN KEY (id_responsavel_especial) REFERENCES usuarios_especiais (id_usuario_especial),
        CONSTRAINT reservas_temporarias_ibfk_3 FOREIGN KEY (id_reserva_local) REFERENCES locais (id_local),
        CONSTRAINT reservas_temporarias_ibfk_4 FOREIGN KEY (id_reserva_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT chk_reserva_inicio_menor_fim CHECK ((`inicio_reserva` <= `fim_reserva`))
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS situacoes_das_reservas (
        id_situacao INTEGER NOT NULL AUTO_INCREMENT,
        id_situacao_local INTEGER NOT NULL,
        id_situacao_aula INTEGER NOT NULL,
        situacao_dia DATE NOT NULL,
        situacao_chave ENUM (
            'NAO_PEGOU_A_CHAVE',
            'PEGOU_A_CHAVE',
            'DEVOLVEU_A_CHAVE'
        ) NOT NULL DEFAULT 'NAO_PEGOU_A_CHAVE',
        tipo_reserva ENUM ('FIXA', 'TEMPORARIA') NOT NULL DEFAULT 'FIXA',
        PRIMARY KEY (id_situacao),
        CONSTRAINT situacoes_das_reservas_ibfk_1 FOREIGN KEY (id_situacao_local) REFERENCES locais (id_local),
        CONSTRAINT situacoes_das_reservas_ibfk_2 FOREIGN KEY (id_situacao_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT uq_situacao_local_aula_dia_tipo UNIQUE (
            id_situacao_local,
            id_situacao_aula,
            situacao_dia,
            tipo_reserva
        )
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    IF NOT EXISTS reservas_equipamentos_items (
        id_item INTEGER NOT NULL AUTO_INCREMENT,
        id_reserva INTEGER NOT NULL,
        id_equipamento INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        PRIMARY KEY (id_item),
        CONSTRAINT reservas_equipamentos_items_ibfk_1 FOREIGN KEY (id_reserva) REFERENCES reservas_equipamentos (id_reserva),
        CONSTRAINT reservas_equipamentos_items_ibfk_2 FOREIGN KEY (id_equipamento) REFERENCES equipamentos (id_equipamento),
        CONSTRAINT uq_reserva_equipamento UNIQUE (id_reserva, id_equipamento)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;