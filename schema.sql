CREATE TABLE
    IF NOT EXISTS aulas (
        id_aula INTEGER NOT NULL AUTO_INCREMENT,
        horario_inicio TIME NOT NULL,
        horario_fim TIME NOT NULL,
        PRIMARY KEY (id_aula),
        CONSTRAINT uq_aula_inicio_fim UNIQUE (horario_inicio, horario_fim)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS dias_da_semana (
        id_semana INTEGER NOT NULL,
        nome_semana VARCHAR(15) NOT NULL,
        PRIMARY KEY (id_semana),
        CONSTRAINT nome_semana UNIQUE (nome_semana)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS locais (
        id_local INTEGER NOT NULL AUTO_INCREMENT,
        nome_local VARCHAR(100) NOT NULL,
        `descrição` TEXT,
        disponibilidade ENUM ('DISPONIVEL', 'INDISPONIVEL') NOT NULL DEFAULT 'DISPONIVEL',
        tipo ENUM ('LABORATORIO', 'SALA', 'EXTERNO', 'AUDITORIO') NOT NULL DEFAULT 'LABORATORIO',
        PRIMARY KEY (id_local),
        CONSTRAINT uq_local UNIQUE (nome_local)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS pessoas (
        id_pessoa INTEGER NOT NULL AUTO_INCREMENT,
        nome_pessoa VARCHAR(100) NOT NULL,
        alias VARCHAR(100),
        email_pessoa VARCHAR(100),
        PRIMARY KEY (id_pessoa)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

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
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS turnos (
        id_turno INTEGER NOT NULL AUTO_INCREMENT,
        nome_turno VARCHAR(15) NOT NULL,
        horario_inicio TIME NOT NULL,
        horario_fim TIME NOT NULL,
        PRIMARY KEY (id_turno),
        CONSTRAINT nome_turno UNIQUE (nome_turno),
        CONSTRAINT uq_turno_inicio_fim UNIQUE (horario_inicio, horario_fim)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS usuarios_especiais (
        id_usuario_especial INTEGER NOT NULL AUTO_INCREMENT,
        nome_usuario_especial VARCHAR(100) NOT NULL,
        PRIMARY KEY (id_usuario_especial),
        CONSTRAINT uq_usuario_especial UNIQUE (nome_usuario_especial)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

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
        ),
        CONSTRAINT unique_aula_semana_tipo UNIQUE (id_aula, id_semana, tipo_aula)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS usuarios (
        id_usuario INTEGER NOT NULL AUTO_INCREMENT,
        id_pessoa INTEGER NOT NULL,
        tipo_pessoa VARCHAR(50) NOT NULL,
        situacao_pessoa VARCHAR(50) NOT NULL,
        grupo_pessoa VARCHAR(50),
        PRIMARY KEY (id_usuario),
        CONSTRAINT usuarios_ibfk_1 FOREIGN KEY (id_pessoa) REFERENCES pessoas (id_pessoa)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS exibicao_reservas (
        id_exibicao INTEGER NOT NULL AUTO_INCREMENT,
        id_exibicao_local INTEGER NOT NULL,
        id_exibicao_aula INTEGER NOT NULL,
        exibicao_dia DATE NOT NULL,
        tipo_reserva ENUM ('FIXA', 'TEMPORARIA') NOT NULL DEFAULT 'TEMPORARIA',
        PRIMARY KEY (id_exibicao),
        CONSTRAINT exibicao_reservas_ibfk_2 FOREIGN KEY (id_exibicao_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT fk_exibicao_reservas_locais FOREIGN KEY (id_exibicao_local) REFERENCES locais (id_local),
        CONSTRAINT uq_exibicao_lab_aula_dia UNIQUE (id_exibicao_local, id_exibicao_aula, exibicao_dia)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

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
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS permissoes (
        id_permissao_usuario INTEGER NOT NULL,
        permissao INTEGER NOT NULL,
        PRIMARY KEY (id_permissao_usuario),
        CONSTRAINT permissoes_ibfk_1 FOREIGN KEY (id_permissao_usuario) REFERENCES usuarios (id_usuario)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS reservas_fixas (
        id_reserva_fixa INTEGER NOT NULL AUTO_INCREMENT,
        id_responsavel INTEGER,
        id_responsavel_especial INTEGER,
        tipo_responsavel INTEGER NOT NULL,
        id_reserva_local INTEGER NOT NULL,
        id_reserva_aula INTEGER NOT NULL,
        id_reserva_semestre INTEGER NOT NULL,
        finalidade_reserva ENUM (
            'GRADUACAO',
            'ESPECIALIZACAO',
            'EAD',
            'NAPTI',
            'CURSO',
            'USO_DOS_ALUNOS'
        ) NOT NULL DEFAULT 'GRADUACAO',
        observacoes TEXT,
        descricao VARCHAR(100),
        PRIMARY KEY (id_reserva_fixa),
        CONSTRAINT fk_reservas_fixas_locais FOREIGN KEY (id_reserva_local) REFERENCES locais (id_local),
        CONSTRAINT reservas_fixas_ibfk_1 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa),
        CONSTRAINT reservas_fixas_ibfk_2 FOREIGN KEY (id_responsavel_especial) REFERENCES usuarios_especiais (id_usuario_especial),
        CONSTRAINT reservas_fixas_ibfk_4 FOREIGN KEY (id_reserva_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT reservas_fixas_ibfk_5 FOREIGN KEY (id_reserva_semestre) REFERENCES semestres (id_semestre),
        CONSTRAINT check_tipo_responsavel_fixa CHECK (
            (
                (
                    (`tipo_responsavel` = 0)
                    and (`id_responsavel` is not null)
                    and (`id_responsavel_especial` is null)
                )
                or (
                    (`tipo_responsavel` = 1)
                    and (`id_responsavel` is null)
                    and (`id_responsavel_especial` is not null)
                )
                or (
                    (`tipo_responsavel` = 2)
                    and (`id_responsavel` is not null)
                    and (`id_responsavel_especial` is not null)
                )
            )
        ),
        CONSTRAINT check_tipo_responsavel_value_fixa CHECK ((`tipo_responsavel` in (0, 1, 2))),
        CONSTRAINT uq_reserva_lab_aula_semestre UNIQUE (
            id_reserva_local,
            id_reserva_aula,
            id_reserva_semestre
        )
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS reservas_temporarias (
        id_reserva_temporaria INTEGER NOT NULL AUTO_INCREMENT,
        id_responsavel INTEGER,
        id_responsavel_especial INTEGER,
        tipo_responsavel INTEGER NOT NULL,
        id_reserva_local INTEGER NOT NULL,
        id_reserva_aula INTEGER NOT NULL,
        inicio_reserva DATE NOT NULL,
        fim_reserva DATE NOT NULL,
        finalidade_reserva ENUM (
            'GRADUACAO',
            'ESPECIALIZACAO',
            'EAD',
            'NAPTI',
            'CURSO',
            'USO_DOS_ALUNOS'
        ) NOT NULL DEFAULT 'GRADUACAO',
        observacoes TEXT,
        descricao VARCHAR(100),
        PRIMARY KEY (id_reserva_temporaria),
        CONSTRAINT fk_reservas_temporarias_locais FOREIGN KEY (id_reserva_local) REFERENCES locais (id_local),
        CONSTRAINT reservas_temporarias_ibfk_1 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa),
        CONSTRAINT reservas_temporarias_ibfk_2 FOREIGN KEY (id_responsavel_especial) REFERENCES usuarios_especiais (id_usuario_especial),
        CONSTRAINT reservas_temporarias_ibfk_4 FOREIGN KEY (id_reserva_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT check_tipo_responsavel_temporaria CHECK (
            (
                (
                    (`tipo_responsavel` = 0)
                    and (`id_responsavel` is not null)
                    and (`id_responsavel_especial` is null)
                )
                or (
                    (`tipo_responsavel` = 1)
                    and (`id_responsavel` is null)
                    and (`id_responsavel_especial` is not null)
                )
                or (
                    (`tipo_responsavel` = 2)
                    and (`id_responsavel` is not null)
                    and (`id_responsavel_especial` is not null)
                )
            )
        ),
        CONSTRAINT check_tipo_responsavel_value_temporaria CHECK ((`tipo_responsavel` in (0, 1, 2))),
        CONSTRAINT chk_reserva_inicio_menor_fim CHECK ((`inicio_reserva` <= `fim_reserva`))
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;

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
        CONSTRAINT fk_situacoes_das_reservas_locais FOREIGN KEY (id_situacao_local) REFERENCES locais (id_local),
        CONSTRAINT situacoes_das_reservas_ibfk_2 FOREIGN KEY (id_situacao_aula) REFERENCES aulas_ativas (id_aula_ativa),
        CONSTRAINT uq_situacao_lab_aula_dia_tipo UNIQUE (
            id_situacao_local,
            id_situacao_aula,
            situacao_dia,
            tipo_reserva
        )
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE utf8mb4_0900_ai_ci;