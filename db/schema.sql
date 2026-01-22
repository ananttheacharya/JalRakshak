/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-12.1.2-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: jalrakshak
-- ------------------------------------------------------
-- Server version	12.1.2-MariaDB

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
-- Table structure for table `alerts`
--

DROP TABLE IF EXISTS `alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `alerts` (
  `alert_id` int(11) NOT NULL AUTO_INCREMENT,
  `node_id` varchar(255) NOT NULL,
  `hierarchy_level` int(11) NOT NULL,
  `alert_level` varchar(10) NOT NULL,
  `cwqi_value` float NOT NULL,
  `reason` text DEFAULT NULL,
  `detected_at` datetime NOT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`alert_id`),
  KEY `idx_node_active` (`node_id`,`is_active`),
  CONSTRAINT `fk_alerts_node` FOREIGN KEY (`node_id`) REFERENCES `nodes` (`node_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1152 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `node_status`
--

DROP TABLE IF EXISTS `node_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `node_status` (
  `node_id` varchar(255) NOT NULL,
  `last_updated` datetime NOT NULL,
  `cwqi` float NOT NULL,
  `status` enum('GREEN','AMBER','RED') NOT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `anomaly_detected` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`node_id`),
  CONSTRAINT `node_status_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `nodes` (`node_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nodes`
--

DROP TABLE IF EXISTS `nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `nodes` (
  `node_id` varchar(255) NOT NULL,
  `hierarchy_level` int(11) NOT NULL,
  `pump` varchar(255) NOT NULL,
  `zone` varchar(255) DEFAULT NULL,
  `colony` varchar(255) DEFAULT NULL,
  `installed_on` date NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `status` enum('GREEN','AMBER','RED') DEFAULT 'GREEN',
  `last_updated` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`node_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sensor_readings`
--

DROP TABLE IF EXISTS `sensor_readings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `sensor_readings` (
  `reading_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `node_id` varchar(255) NOT NULL,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp(),
  `turbidity` float DEFAULT NULL,
  `ph` float DEFAULT NULL,
  `fluoride` float DEFAULT NULL,
  `coliform` int(11) DEFAULT NULL,
  `conductivity` float DEFAULT NULL,
  `temperature` float DEFAULT NULL,
  `dissolved_oxygen` float DEFAULT NULL,
  `pressure` float DEFAULT NULL,
  `flow_rate` float DEFAULT NULL,
  PRIMARY KEY (`reading_id`),
  KEY `idx_node_time` (`node_id`,`timestamp`),
  KEY `idx_time` (`timestamp`),
  CONSTRAINT `sensor_readings_ibfk_1` FOREIGN KEY (`node_id`) REFERENCES `nodes` (`node_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=230273 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `staging_supply_raw`
--

DROP TABLE IF EXISTS `staging_supply_raw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `staging_supply_raw` (
  `pump` varchar(255) DEFAULT NULL,
  `zone` varchar(255) DEFAULT NULL,
  `colony` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `supply_clean`
--

DROP TABLE IF EXISTS `supply_clean`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `supply_clean` (
  `pump` varchar(255) DEFAULT NULL,
  `zone` varchar(255) DEFAULT NULL,
  `colony` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `supply_deduped`
--

DROP TABLE IF EXISTS `supply_deduped`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `supply_deduped` (
  `pump` varchar(255) DEFAULT NULL,
  `zone` varchar(255) DEFAULT NULL,
  `colony` varchar(255) DEFAULT NULL,
  `row_id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`row_id`)
) ENGINE=InnoDB AUTO_INCREMENT=485 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `supply_zone_filled`
--

DROP TABLE IF EXISTS `supply_zone_filled`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `supply_zone_filled` (
  `pump` varchar(255) DEFAULT NULL,
  `zone` varchar(255) DEFAULT NULL,
  `colony` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `supply_zone_filled1`
--

DROP TABLE IF EXISTS `supply_zone_filled1`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `supply_zone_filled1` (
  `pump` varchar(255) DEFAULT NULL,
  `zone` varchar(255) DEFAULT NULL,
  `colony` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-01-22 23:55:02
