CREATE TABLE
    IF NOT EXISTS `aulas` (
        `id_aula` int NOT NULL AUTO_INCREMENT,
        `horario_inicio` time NOT NULL,
        `horario_fim` time NOT NULL,
        PRIMARY KEY (`id_aula`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `aulas_ativas` (
        `id_aula_ativa` int NOT NULL AUTO_INCREMENT,
        `id_aula` int NOT NULL,
        `inicio_ativacao` date DEFAULT NULL,
        `fim_ativacao` date DEFAULT NULL,
        `semana` int DEFAULT NULL,
        `turno` int DEFAULT NULL,
        `tipo_aula` int NOT NULL DEFAULT '0',
        PRIMARY KEY (`id_aula_ativa`),
        KEY `id_aula` (`id_aula`),
        CONSTRAINT `aulas_ativas_ibfk_1` FOREIGN KEY (`id_aula`) REFERENCES `aulas` (`id_aula`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `laboratorios` (
        `id_laboratorio` int NOT NULL AUTO_INCREMENT,
        `nome_laboratorio` varchar(100) NOT NULL,
        `disponibilidade` enum ('DISPONIVEL', 'INDISPONIVEL') NOT NULL DEFAULT 'DISPONIVEL',
        `tipo` enum ('LABORATORIO', 'SALA', 'EXTERNO') NOT NULL DEFAULT 'LABORATORIO',
        PRIMARY KEY (`id_laboratorio`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `pessoas` (
        `id_pessoa` int NOT NULL AUTO_INCREMENT,
        `nome_pessoa` varchar(100) NOT NULL,
        `email_pessoa` varchar(100) DEFAULT NULL,
        PRIMARY KEY (`id_pessoa`)
    ) ENGINE = InnoDB AUTO_INCREMENT = 2 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `usuarios` (
        `id_usuario` int NOT NULL AUTO_INCREMENT,
        `id_pessoa` int NOT NULL,
        `tipo_pessoa` varchar(50) NOT NULL,
        `situacao_pessoa` varchar(50) NOT NULL,
        `grupo_pessoa` varchar(50) DEFAULT NULL,
        PRIMARY KEY (`id_usuario`),
        KEY `id_pessoa` (`id_pessoa`),
        CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_pessoa`) REFERENCES `pessoas` (`id_pessoa`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `historicos` (
        `id_historico` int NOT NULL AUTO_INCREMENT,
        `id_usuario` int NOT NULL,
        `id_pessoa` int NOT NULL,
        `tabela` varchar(100) DEFAULT NULL,
        `categoria` varchar(100) DEFAULT NULL,
        `data_hora` datetime NOT NULL,
        `message` text NOT NULL,
        `chave_primaria` text NOT NULL,
        `observacao` text,
        PRIMARY KEY (`id_historico`),
        KEY `id_usuario` (`id_usuario`),
        KEY `id_pessoa` (`id_pessoa`),
        KEY `ix_historicos_tabela` (`tabela`),
        KEY `ix_historicos_data_hora` (`data_hora`),
        CONSTRAINT `historicos_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`),
        CONSTRAINT `historicos_ibfk_2` FOREIGN KEY (`id_pessoa`) REFERENCES `pessoas` (`id_pessoa`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `permissoes` (
        `id_permissao_usuario` int NOT NULL,
        `permissao` int NOT NULL,
        PRIMARY KEY (`id_permissao_usuario`),
        CONSTRAINT `permissoes_ibfk_1` FOREIGN KEY (`id_permissao_usuario`) REFERENCES `usuarios` (`id_usuario`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `usuarios_especiais` (
        `id_usuario_especial` int NOT NULL AUTO_INCREMENT,
        `nome_usuario_especial` varchar(100) NOT NULL,
        PRIMARY KEY (`id_usuario_especial`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `semestres` (
        `id_semestre` int NOT NULL AUTO_INCREMENT,
        `data_inicio` date NOT NULL,
        `data_fim` date NOT NULL,
        PRIMARY KEY (`id_semestre`)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE
    IF NOT EXISTS `reservas_fixas` (
        `id_reserva_fixa` int NOT NULL AUTO_INCREMENT,
        `id_responsavel` int DEFAULT NULL,
        `id_responsavel_especial` int DEFAULT NULL,
        `tipo_responsavel` int NOT NULL,
        `id_reserva_laboratorio` int NOT NULL,
        `id_reserva_aula` int NOT NULL,
        `status_reserva` int NOT NULL DEFAULT '0',
        `tipo` int NOT NULL DEFAULT '0',
        `id_reserva_semestre` int NOT NULL,
        PRIMARY KEY (`id_reserva_fixa`),
        UNIQUE KEY `uq_reserva_lab_aula_semestre` (
            `id_reserva_laboratorio`,
            `id_reserva_aula`,
            `id_reserva_semestre`
        ),
        KEY `id_responsavel` (`id_responsavel`),
        KEY `id_responsavel_especial` (`id_responsavel_especial`),
        KEY `id_reserva_aula` (`id_reserva_aula`),
        KEY `id_reserva_semestre` (`id_reserva_semestre`),
        CONSTRAINT `reservas_fixas_ibfk_1` FOREIGN KEY (`id_responsavel`) REFERENCES `pessoas` (`id_pessoa`),
        CONSTRAINT `reservas_fixas_ibfk_2` FOREIGN KEY (`id_responsavel_especial`) REFERENCES `usuarios_especiais` (`id_usuario_especial`),
        CONSTRAINT `reservas_fixas_ibfk_3` FOREIGN KEY (`id_reserva_laboratorio`) REFERENCES `laboratorios` (`id_laboratorio`),
        CONSTRAINT `reservas_fixas_ibfk_4` FOREIGN KEY (`id_reserva_aula`) REFERENCES `aulas_ativas` (`id_aula_ativa`),
        CONSTRAINT `reservas_fixas_ibfk_5` FOREIGN KEY (`id_reserva_semestre`) REFERENCES `semestres` (`id_semestre`),
        CONSTRAINT `check_tipo_responsavel` CHECK (
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
        )
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;