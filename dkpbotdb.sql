-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               8.0.42 - MySQL Community Server - GPL
-- Server OS:                    Win64
-- HeidiSQL Version:             12.10.0.7000
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for dkpbot
CREATE DATABASE IF NOT EXISTS `dkpbot` /*!40100 DEFAULT CHARACTER SET latin1 */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `dkpbot`;

-- Dumping structure for table dkpbot.attendance
CREATE TABLE IF NOT EXISTS `attendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `granted_by` varchar(100) DEFAULT 'Nobody',
  `reason` varchar(150) DEFAULT 'None',
  KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.attendance: ~0 rows (approximately)
DELETE FROM `attendance`;

-- Dumping structure for table dkpbot.attendance_ticks
CREATE TABLE IF NOT EXISTS `attendance_ticks` (
  `discord_id` bigint DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.attendance_ticks: ~0 rows (approximately)
DELETE FROM `attendance_ticks`;

-- Dumping structure for table dkpbot.bids
CREATE TABLE IF NOT EXISTS `bids` (
  `item_name` varchar(100) DEFAULT NULL,
  `channel_id` varchar(50) DEFAULT NULL,
  `top_bidder` varchar(100) DEFAULT NULL,
  `top_bid_amt` int DEFAULT '0',
  `second_bidder` varchar(100) DEFAULT NULL,
  `second_bid_amt` int DEFAULT '0',
  `timeout_reset` int DEFAULT '30',
  `timeout` varchar(100) DEFAULT '0',
  `main_has_bid` int DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.bids: ~0 rows (approximately)
DELETE FROM `bids`;

-- Dumping structure for table dkpbot.bot_channels
CREATE TABLE IF NOT EXISTS `bot_channels` (
  `type` varchar(100) DEFAULT NULL,
  `value` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.bot_channels: ~0 rows (approximately)
DELETE FROM `bot_channels`;

-- Dumping structure for table dkpbot.completed_bids
CREATE TABLE IF NOT EXISTS `completed_bids` (
  `item_name` varchar(100) DEFAULT NULL,
  `winner` varchar(100) DEFAULT NULL,
  `dkp_cost` int DEFAULT NULL,
  `second_place` varchar(100) DEFAULT NULL,
  `second_place_bid` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.completed_bids: ~0 rows (approximately)
DELETE FROM `completed_bids`;

-- Dumping structure for table dkpbot.dkp
CREATE TABLE IF NOT EXISTS `dkp` (
  `discord_id` bigint DEFAULT NULL,
  `main_name` varchar(100) DEFAULT NULL,
  `dkp_value` int DEFAULT '0',
  `character_class` varchar(50) DEFAULT 'NOT_SET',
  `time_registered` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `discord_id` (`discord_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.dkp: ~0 rows (approximately)
DELETE FROM `dkp`;

-- Dumping structure for table dkpbot.rolls
CREATE TABLE IF NOT EXISTS `rolls` (
  `item_name` varchar(100) DEFAULT NULL,
  `channel_id` bigint DEFAULT NULL,
  `winner_id` bigint DEFAULT NULL,
  `second_id` bigint DEFAULT NULL,
  `winner_roll` int DEFAULT '0',
  `second_roll` int DEFAULT '0',
  `main_has_rolled` int DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.rolls: ~0 rows (approximately)
DELETE FROM `rolls`;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
