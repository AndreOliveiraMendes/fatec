-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: localhost    Database: laboratorio
-- ------------------------------------------------------
-- Server version	8.0.42-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `aulas`
--

DROP TABLE IF EXISTS `aulas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `aulas` (
  `id_aula` int NOT NULL AUTO_INCREMENT,
  `horario_inicio` time DEFAULT NULL,
  `horario_fim` time DEFAULT NULL,
  `semana` int DEFAULT NULL,
  `turno` int DEFAULT NULL,
  PRIMARY KEY (`id_aula`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `aulas_ativas`
--

DROP TABLE IF EXISTS `aulas_ativas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `aulas_ativas` (
  `id_aula_ativa` int NOT NULL AUTO_INCREMENT,
  `inicio_ativacao` date DEFAULT NULL,
  `fim_ativacao` date DEFAULT NULL,
  PRIMARY KEY (`id_aula_ativa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cursos`
--

DROP TABLE IF EXISTS `cursos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cursos` (
  `id_curso` int NOT NULL AUTO_INCREMENT,
  `nome_curso` varchar(100) NOT NULL,
  PRIMARY KEY (`id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `historicos`
--

DROP TABLE IF EXISTS `historicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historicos` (
  `id_historico` int NOT NULL AUTO_INCREMENT,
  `id_pessoa` int NOT NULL,
  `dia` datetime NOT NULL,
  `acao` text NOT NULL,
  `observacao` text,
  PRIMARY KEY (`id_historico`),
  KEY `id_pessoa` (`id_pessoa`),
  CONSTRAINT `historicos_ibfk_1` FOREIGN KEY (`id_pessoa`) REFERENCES `pessoas` (`id_pessoa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `laboratorios`
--

DROP TABLE IF EXISTS `laboratorios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `laboratorios` (
  `id_laboratorio` int NOT NULL AUTO_INCREMENT,
  `nome_laboratorio` varchar(100) NOT NULL,
  `disponibilidade` int DEFAULT NULL,
  `tipo` int DEFAULT '0',
  PRIMARY KEY (`id_laboratorio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `permissoes`
--

DROP TABLE IF EXISTS `permissoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissoes` (
  `id_permissao_usuario` int NOT NULL,
  `permissao` int NOT NULL,
  PRIMARY KEY (`id_permissao_usuario`),
  CONSTRAINT `permissoes_ibfk_1` FOREIGN KEY (`id_permissao_usuario`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pessoas`
--

DROP TABLE IF EXISTS `pessoas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pessoas` (
  `id_pessoa` int NOT NULL AUTO_INCREMENT,
  `nome_pessoa` varchar(100) NOT NULL,
  `email_pessoa` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_pessoa`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `reservas_fixas`
--

DROP TABLE IF EXISTS `reservas_fixas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservas_fixas` (
  `id_reserva_fixa` int NOT NULL AUTO_INCREMENT,
  `id_responsavel` int DEFAULT NULL,
  `id_curso` int DEFAULT NULL,
  `tipo_responsavel` int NOT NULL,
  `id_reserva_laboratorio` int NOT NULL,
  `id_reserva_aula` int NOT NULL,
  `status_reserva` int NOT NULL DEFAULT '0',
  `data_inicio` date NOT NULL,
  `data_fim` date NOT NULL,
  PRIMARY KEY (`id_reserva_fixa`),
  KEY `id_responsavel` (`id_responsavel`),
  KEY `id_curso` (`id_curso`),
  KEY `id_reserva_laboratorio` (`id_reserva_laboratorio`),
  KEY `id_reserva_aula` (`id_reserva_aula`),
  CONSTRAINT `reservas_fixas_ibfk_1` FOREIGN KEY (`id_responsavel`) REFERENCES `pessoas` (`id_pessoa`),
  CONSTRAINT `reservas_fixas_ibfk_2` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id_curso`),
  CONSTRAINT `reservas_fixas_ibfk_3` FOREIGN KEY (`id_reserva_laboratorio`) REFERENCES `laboratorios` (`id_laboratorio`),
  CONSTRAINT `reservas_fixas_ibfk_4` FOREIGN KEY (`id_reserva_aula`) REFERENCES `aulas` (`id_aula`),
  CONSTRAINT `check_tipo_responsavel` CHECK ((((`tipo_responsavel` = 0) and (`id_responsavel` is not null) and (`id_curso` is null)) or ((`tipo_responsavel` = 1) and (`id_responsavel` is null) and (`id_curso` is not null)) or ((`tipo_responsavel` = 2) and (`id_responsavel` is not null) and (`id_curso` is not null))))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `id_pessoa` int NOT NULL,
  `tipo_pessoa` varchar(50) DEFAULT NULL,
  `situacao_pessoa` varchar(50) DEFAULT NULL,
  `grupo_pessoa` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  KEY `id_pessoa` (`id_pessoa`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_pessoa`) REFERENCES `pessoas` (`id_pessoa`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-23 18:42:14
