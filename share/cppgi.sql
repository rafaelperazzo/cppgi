/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.6-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: cppgi
-- ------------------------------------------------------
-- Server version	11.8.6-MariaDB-ubu2404

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `acessos`
--

DROP TABLE IF EXISTS `acessos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `acessos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `data` datetime NOT NULL DEFAULT current_timestamp(),
  `ip` varchar(20) NOT NULL DEFAULT '0.0.0.0',
  `recurso` varchar(30) NOT NULL DEFAULT 'n/a',
  `username` varchar(20) NOT NULL DEFAULT 'indefinido',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22375 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `avaliacoes`
--

DROP TABLE IF EXISTS `avaliacoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `avaliacoes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `idProjeto` int(11) NOT NULL,
  `token` varchar(50) NOT NULL,
  `avaliador` varchar(100) NOT NULL,
  `nome_avaliador` varchar(100) NOT NULL DEFAULT 'NAO INFORMADO',
  `c1` int(11) NOT NULL DEFAULT 0 COMMENT 'critério A',
  `c2` int(11) NOT NULL DEFAULT 0 COMMENT 'critério B',
  `c3` int(11) NOT NULL DEFAULT 0 COMMENT 'critério C',
  `c4` int(11) NOT NULL DEFAULT 0 COMMENT 'critério D',
  `c5` int(11) NOT NULL DEFAULT 0 COMMENT 'critério E',
  `c6` int(11) NOT NULL DEFAULT 0 COMMENT 'critério F',
  `c7` int(11) NOT NULL DEFAULT 0 COMMENT 'critério G',
  `c8` int(11) NOT NULL DEFAULT 0,
  `c9` int(11) NOT NULL DEFAULT 0,
  `cepa` int(11) NOT NULL DEFAULT -1 COMMENT 'Precisa de Comite de Ética ?',
  `identificado` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Não identificado; 1 - identificado',
  `comentario` text DEFAULT NULL,
  `recomendacao` int(11) DEFAULT -1 COMMENT '0 - Não recomendado; 1 - Recomendado',
  `link` varchar(200) NOT NULL,
  `enviado` int(11) NOT NULL DEFAULT 0 COMMENT '0: Não enviado; 1: Enviado',
  `aceitou` int(11) NOT NULL DEFAULT -1 COMMENT '1: Sim; 0: Não',
  `finalizado` int(11) NOT NULL DEFAULT 0 COMMENT '0: Não finalizado; 1: Finalizado',
  `data_envio` timestamp NULL DEFAULT NULL,
  `data_envio2` timestamp NULL DEFAULT '0000-00-00 00:00:00',
  `data_avaliacao` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `UnicoProjetoToken` (`idProjeto`,`token`),
  CONSTRAINT `avaliacoes_ibfk_1` FOREIGN KEY (`idProjeto`) REFERENCES `editalProjeto` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12985 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `avaliacoes_orais`
--

DROP TABLE IF EXISTS `avaliacoes_orais`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `avaliacoes_orais` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `idProjeto` int(11) NOT NULL,
  `avaliador` varchar(200) NOT NULL DEFAULT 'NÃO INFORMADO',
  `c1` int(11) NOT NULL DEFAULT 0,
  `c2` int(11) NOT NULL DEFAULT 0,
  `c3` int(11) NOT NULL DEFAULT 0,
  `c4` int(11) NOT NULL DEFAULT 0,
  `comentarios` text NOT NULL,
  `data` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idProjeto` (`idProjeto`),
  CONSTRAINT `idProjeto` FOREIGN KEY (`idProjeto`) REFERENCES `editalProjeto` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2455 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `certificados_moderador`
--

DROP TABLE IF EXISTS `certificados_moderador`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `certificados_moderador` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `edital` int(11) NOT NULL DEFAULT 7,
  `nome` varchar(500) NOT NULL,
  `tipo` varchar(500) NOT NULL,
  `token` varchar(100) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4689 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `declaracoes`
--

DROP TABLE IF EXISTS `declaracoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `declaracoes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(200) NOT NULL,
  `siape` int(11) NOT NULL,
  `evento` varchar(200) NOT NULL,
  `participacao` varchar(200) NOT NULL,
  `periodo` varchar(200) NOT NULL,
  `local` varchar(200) NOT NULL,
  `modalidade` varchar(200) NOT NULL,
  `email` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `editais`
--

DROP TABLE IF EXISTS `editais`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `editais` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_uca1400_ai_ci NOT NULL,
  `nome_curto` varchar(100) NOT NULL DEFAULT 'CPPGI',
  `nome_longo` varchar(150) NOT NULL DEFAULT 'CONGRESSO DE PESQUISA, PÓS-GRADUAÇÃO E INOVAÇÃO',
  `periodo` varchar(200) NOT NULL DEFAULT 'N/A',
  `local` varchar(200) NOT NULL DEFAULT 'Universidade Federal do Cariri/UFCA em Juazeiro do Norte, Ceará',
  `deadline` datetime NOT NULL,
  `deadline_avaliacao` timestamp NOT NULL DEFAULT current_timestamp(),
  `deadline_apresentacao` datetime NOT NULL,
  `deadline_versao_final` datetime NOT NULL,
  `quantidade_bolsas` int(11) NOT NULL DEFAULT 0,
  `quantidade_bolsas_cnpq` int(11) NOT NULL DEFAULT 0,
  `setor` int(11) NOT NULL,
  `auxilio_financeiro` float NOT NULL DEFAULT 0,
  `agradecimento` int(11) NOT NULL DEFAULT 0,
  `mensagem` text NOT NULL,
  `recursos` varchar(200) NOT NULL DEFAULT 'N/A',
  `link` varchar(150) NOT NULL DEFAULT 'N/A',
  `carta_convite` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_uca1400_ai_ci NOT NULL DEFAULT 'INDEFINIDO',
  `carta_agradecimento` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_uca1400_ai_ci NOT NULL DEFAULT 'INDEFINIDO',
  `declaracao_avaliador` varchar(200) NOT NULL DEFAULT '',
  `certificado_moderador` varchar(50) NOT NULL DEFAULT '',
  `certificado_apresentador` varchar(50) NOT NULL DEFAULT '',
  `certificado_participante` varchar(50) NOT NULL DEFAULT '',
  `certificado_demais` varchar(100) NOT NULL DEFAULT '',
  `certificado_convidado` varchar(50) NOT NULL DEFAULT '',
  `editalAnterior` int(11) NOT NULL DEFAULT -1,
  `classificacao` int(11) NOT NULL DEFAULT 1 COMMENT '1 - Por UA; 2 - Geral',
  `situacao` varchar(100) NOT NULL DEFAULT 'N/A',
  `inicio_versao_final` datetime NOT NULL DEFAULT current_timestamp() COMMENT 'data de início de recebimento de versão final',
  `fim_versao_final` datetime NOT NULL DEFAULT current_timestamp() COMMENT 'data de término de recebimento de versão final',
  `token` varchar(50) NOT NULL,
  `logo` varchar(50) NOT NULL DEFAULT 'logo_cppgi.jpg',
  `isbn` varchar(30) NOT NULL DEFAULT '978-65-88329-04-7',
  `ficha` varchar(30) NOT NULL DEFAULT 'cppgi_ficha.png',
  PRIMARY KEY (`id`),
  KEY `indiceSetor` (`setor`),
  CONSTRAINT `editais_ibfk_1` FOREIGN KEY (`setor`) REFERENCES `setores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2374 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `editalProjeto`
--

DROP TABLE IF EXISTS `editalProjeto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `editalProjeto` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `idProjeto` int(11) NOT NULL DEFAULT 0 COMMENT 'id do projeto de pesquisa associado, se houver',
  `tipo` int(11) NOT NULL COMMENT 'Código do edital (numérico)',
  `categoria` int(11) NOT NULL COMMENT '0 - apresentação oral; 1 - poster',
  `categoria_trabalho` int(11) NOT NULL DEFAULT 1 COMMENT '1 - Iniciação Científica; 2 - Desenvolvimento tecnológico e Inovação; 3 - Ensino Médio; 4 - Pós-Graduação',
  `modalidade` int(11) NOT NULL DEFAULT 1 COMMENT '0 - Resumo simples; 1 - resumo expandido; 2 - trabalho completo',
  `nome` varchar(1000) NOT NULL,
  `siape` varchar(20) NOT NULL,
  `email` varchar(100) NOT NULL,
  `produtividade` int(11) DEFAULT 9 COMMENT '0 - CNPq; 1 - BPI Funcap; 9 - Nenhum',
  `ua` varchar(100) NOT NULL DEFAULT 'N/A',
  `unidade` varchar(100) NOT NULL DEFAULT 'N/A',
  `ods` varchar(100) NOT NULL DEFAULT 'N/A',
  `scorelattes` float DEFAULT 0,
  `scorelattes_detalhado` text DEFAULT NULL,
  `area_capes` varchar(100) DEFAULT NULL,
  `grande_area` varchar(100) DEFAULT NULL,
  `grupo` varchar(200) DEFAULT NULL,
  `arquivo_lattes` varchar(50) DEFAULT NULL,
  `titulo` varchar(500) DEFAULT NULL,
  `validade` int(11) DEFAULT 3,
  `palavras` varchar(200) DEFAULT NULL,
  `resumo` text DEFAULT NULL,
  `vinculo` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Graduação; 1 - Pós ; 2- EM',
  `tipo_vinculo` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Não se aplica; 1 - Bolsista; 2 - Voluntário',
  `fomento` int(11) NOT NULL DEFAULT -1 COMMENT '-1 - sem fomento; 0 - ufca; 1 - cnpq; 2 - funcap',
  `area_cnpq` varchar(50) NOT NULL DEFAULT '',
  `subarea_cnpq` varchar(50) NOT NULL DEFAULT '',
  `matriculas` varchar(100) NOT NULL DEFAULT '',
  `inicio` date DEFAULT NULL,
  `fim` date DEFAULT NULL,
  `bolsas` int(11) DEFAULT 0,
  `bolsas_concedidas` int(11) DEFAULT 0,
  `acessibilidade` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Sem necessidade; 1- com necessidade',
  `descricao_acessibilidade` text NOT NULL DEFAULT 'N/A',
  `lingua` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Portugues; 1 - Libras',
  `arquivo_projeto` varchar(100) DEFAULT '0',
  `arquivo_projeto_final` varchar(200) NOT NULL DEFAULT '0',
  `arquivo_plano1` varchar(100) DEFAULT '0',
  `arquivo_plano2` varchar(100) DEFAULT '0',
  `arquivo_lattes_pdf` varchar(200) DEFAULT '0',
  `arquivo_comprovantes` varchar(200) DEFAULT '0',
  `transporte` int(11) NOT NULL DEFAULT 0,
  `data` datetime NOT NULL DEFAULT current_timestamp(),
  `situacao` int(11) DEFAULT -1 COMMENT '-1: Não avaliado; 0; Não recomendado; 1 - Recomendado',
  `valendo` int(11) NOT NULL DEFAULT 1,
  `obs` varchar(300) NOT NULL DEFAULT 'N/A',
  `apresentou` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Não apresentou; 1 - Apresentou; 2- justificou',
  `local_apresentacao` varchar(200) NOT NULL DEFAULT '-',
  `data_apresentacao` datetime DEFAULT NULL,
  `media1` float NOT NULL DEFAULT 0,
  `media2` float NOT NULL DEFAULT 0,
  `premiacao` int(11) NOT NULL DEFAULT 0,
  `token` varchar(100) NOT NULL DEFAULT '0',
  `link_apresentacao` varchar(300) NOT NULL DEFAULT '0',
  `anais` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1584 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sala_link`
--

DROP TABLE IF EXISTS `sala_link`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sala_link` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sala` varchar(10) NOT NULL,
  `link` varchar(200) NOT NULL,
  `edital` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=115 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `salas`
--

DROP TABLE IF EXISTS `salas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `salas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `edital` int(11) NOT NULL,
  `tipo` int(11) NOT NULL DEFAULT 0 COMMENT '0 - oral; 1 - poster',
  `dia` date NOT NULL,
  `inicio` time NOT NULL,
  `termino` time NOT NULL,
  `slot` int(11) NOT NULL DEFAULT 10,
  `salas` varchar(500) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sessoes_ativas`
--

DROP TABLE IF EXISTS `sessoes_ativas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sessoes_ativas` (
  `username` varchar(20) NOT NULL,
  `nome` varchar(100) NOT NULL DEFAULT '',
  `ip` varchar(45) NOT NULL DEFAULT '0.0.0.0',
  `rota` varchar(100) NOT NULL DEFAULT '',
  `ultimo_acesso` datetime NOT NULL,
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `setores`
--

DROP TABLE IF EXISTS `setores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `setores` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `descricao` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `subcnpq`
--

DROP TABLE IF EXISTS `subcnpq`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `subcnpq` (
  `id` int(2) DEFAULT NULL,
  `descricao` varchar(42) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `password` varchar(200) NOT NULL,
  `permission` int(11) NOT NULL DEFAULT 1 COMMENT '0 - admin; 1 - normal',
  `roles` varchar(200) NOT NULL DEFAULT 'user',
  `nome` varchar(100) NOT NULL DEFAULT 'indefinido',
  `email` varchar(100) NOT NULL DEFAULT 'indefinido',
  `email_verificado` tinyint(1) NOT NULL DEFAULT 0,
  `token_verificacao` varchar(64) DEFAULT NULL,
  `token_verificacao_expira` datetime DEFAULT NULL,
  `forcar_troca_senha` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unico_username` (`username`),
  UNIQUE KEY `unico_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3917 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_backup`
--

DROP TABLE IF EXISTS `users_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_backup` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `password` varchar(200) NOT NULL,
  `permission` int(11) NOT NULL DEFAULT 1 COMMENT '0 - admin; 1 - normal',
  `nome` varchar(100) NOT NULL DEFAULT 'indefinido',
  `email` varchar(100) NOT NULL DEFAULT 'indefinido',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unico_username` (`username`),
  UNIQUE KEY `unico_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=1962 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios_salas`
--

DROP TABLE IF EXISTS `usuarios_salas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_salas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `edital` int(11) NOT NULL,
  `sala` varchar(10) NOT NULL,
  `data` date NOT NULL,
  `area` varchar(200) NOT NULL DEFAULT '-',
  `compareceu` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `username` (`username`),
  CONSTRAINT `username` FOREIGN KEY (`username`) REFERENCES `users` (`username`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=391 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-09-02 10:34:51
