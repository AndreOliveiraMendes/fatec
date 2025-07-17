CREATE TABLE
    aulas (
        id_aula INTEGER NOT NULL AUTO_INCREMENT,
        horario_inicio TIME NOT NULL,
        horario_fim TIME NOT NULL,
        PRIMARY KEY (id_aula)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    dias_da_semana (
        id_semana INTEGER NOT NULL,
        nome_semana VARCHAR(15) NOT NULL,
        PRIMARY KEY (id_semana)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    laboratorios (
        id_laboratorio INTEGER NOT NULL AUTO_INCREMENT,
        nome_laboratorio VARCHAR(100) NOT NULL,
        disponibilidade ENUM ('DISPONIVEL', 'INDISPONIVEL') NOT NULL DEFAULT 'DISPONIVEL',
        tipo ENUM ('LABORATORIO', 'SALA', 'EXTERNO') NOT NULL DEFAULT 'LABORATORIO',
        PRIMARY KEY (id_laboratorio)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    pessoas (
        id_pessoa INTEGER NOT NULL AUTO_INCREMENT,
        nome_pessoa VARCHAR(100) NOT NULL,
        email_pessoa VARCHAR(100),
        PRIMARY KEY (id_pessoa)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    semestres (
        id_semestre INTEGER NOT NULL AUTO_INCREMENT,
        nome_semestre VARCHAR(100) NOT NULL,
        data_inicio DATE NOT NULL,
        data_fim DATE NOT NULL,
        PRIMARY KEY (id_semestre)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    turnos (
        id_turno INTEGER NOT NULL AUTO_INCREMENT,
        nome_turno VARCHAR(15) NOT NULL,
        horario_inicio TIME NOT NULL,
        horario_fim TIME NOT NULL,
        PRIMARY KEY (id_turno)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    usuarios_especiais (
        id_usuario_especial INTEGER NOT NULL AUTO_INCREMENT,
        nome_usuario_especial VARCHAR(100) NOT NULL,
        PRIMARY KEY (id_usuario_especial)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    aulas_ativas (
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
    usuarios (
        id_usuario INTEGER NOT NULL AUTO_INCREMENT,
        id_pessoa INTEGER NOT NULL,
        tipo_pessoa VARCHAR(50) NOT NULL,
        situacao_pessoa VARCHAR(50) NOT NULL,
        grupo_pessoa VARCHAR(50),
        PRIMARY KEY (id_usuario),
        CONSTRAINT usuarios_ibfk_1 FOREIGN KEY (id_pessoa) REFERENCES pessoas (id_pessoa)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    historicos (
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
    permissoes (
        id_permissao_usuario INTEGER NOT NULL,
        permissao INTEGER NOT NULL,
        PRIMARY KEY (id_permissao_usuario),
        CONSTRAINT permissoes_ibfk_1 FOREIGN KEY (id_permissao_usuario) REFERENCES usuarios (id_usuario)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    reservas_fixas (
        id_reserva_fixa INTEGER NOT NULL AUTO_INCREMENT,
        id_responsavel INTEGER,
        id_responsavel_especial INTEGER,
        tipo_responsavel INTEGER NOT NULL,
        id_reserva_laboratorio INTEGER NOT NULL,
        id_reserva_aula INTEGER NOT NULL,
        id_reserva_semestre INTEGER NOT NULL,
        tipo_reserva ENUM (
            'GRADUACAO',
            'ESPECIALIZACAO',
            'EAD',
            'NAPTI',
            'CURSO',
            'USO_DOS_ALUNOS'
        ) NOT NULL DEFAULT 'GRADUACAO',
        PRIMARY KEY (id_reserva_fixa),
        CONSTRAINT reservas_fixas_ibfk_1 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa),
        CONSTRAINT reservas_fixas_ibfk_2 FOREIGN KEY (id_responsavel_especial) REFERENCES usuarios_especiais (id_usuario_especial),
        CONSTRAINT reservas_fixas_ibfk_3 FOREIGN KEY (id_reserva_laboratorio) REFERENCES laboratorios (id_laboratorio),
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
        CONSTRAINT check_tipo_responsavel_value_fixa CHECK ((`tipo_responsavel` in (0, 1, 2)))
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    reservas_temporarias (
        id_reserva_temporaria INTEGER NOT NULL AUTO_INCREMENT,
        id_responsavel INTEGER,
        id_responsavel_especial INTEGER,
        tipo_responsavel INTEGER NOT NULL,
        id_reserva_laboratorio INTEGER NOT NULL,
        id_reserva_aula INTEGER NOT NULL,
        inicio_reserva DATE NOT NULL,
        fim_reserva DATE NOT NULL,
        tipo_reserva ENUM (
            'GRADUACAO',
            'ESPECIALIZACAO',
            'EAD',
            'NAPTI',
            'CURSO',
            'USO_DOS_ALUNOS'
        ) NOT NULL DEFAULT 'GRADUACAO',
        PRIMARY KEY (id_reserva_temporaria),
        CONSTRAINT reservas_temporarias_ibfk_1 FOREIGN KEY (id_responsavel) REFERENCES pessoas (id_pessoa),
        CONSTRAINT reservas_temporarias_ibfk_2 FOREIGN KEY (id_responsavel_especial) REFERENCES usuarios_especiais (id_usuario_especial),
        CONSTRAINT reservas_temporarias_ibfk_3 FOREIGN KEY (id_reserva_laboratorio) REFERENCES laboratorios (id_laboratorio),
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
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;

CREATE TABLE
    situacoes_das_reservas (
        id_situacao INTEGER NOT NULL AUTO_INCREMENT,
        id_laboratorio INTEGER NOT NULL,
        id_aula INTEGER NOT NULL,
        dia DATE NOT NULL,
        situacao_chave ENUM (
            'NAO_PEGOU_A_CHAVE',
            'PEGOU_A_CHAVE',
            'DEVOLVEU_A_CHAVE'
        ) NOT NULL DEFAULT 'NAO_PEGOU_A_CHAVE',
        PRIMARY KEY (id_situacao),
        CONSTRAINT situacoes_das_reservas_ibfk_1 FOREIGN KEY (id_laboratorio) REFERENCES laboratorios (id_laboratorio),
        CONSTRAINT situacoes_das_reservas_ibfk_2 FOREIGN KEY (id_aula) REFERENCES aulas_ativas (id_aula_ativa)
    ) ENGINE = InnoDB COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET = utf8mb4;