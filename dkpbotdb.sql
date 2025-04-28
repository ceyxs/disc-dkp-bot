-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               10.0.21-MariaDB - mariadb.org binary distribution
-- Server OS:                    Win64
-- HeidiSQL Version:             9.1.0.4867
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;

-- Dumping database structure for dkpbot
CREATE DATABASE IF NOT EXISTS `dkpbot` /*!40100 DEFAULT CHARACTER SET latin1 */;
USE `dkpbot`;


-- Dumping structure for table dkpbot.attendance
CREATE TABLE IF NOT EXISTS `attendance` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `granted_by` varchar(100) DEFAULT 'Nobody',
  `reason` varchar(150) DEFAULT 'None',
  KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.attendance: ~3 rows (approximately)
/*!40000 ALTER TABLE `attendance` DISABLE KEYS */;
/*!40000 ALTER TABLE `attendance` ENABLE KEYS */;


-- Dumping structure for table dkpbot.attendance_ticks
CREATE TABLE IF NOT EXISTS `attendance_ticks` (
  `discord_id` bigint(20) DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.attendance_ticks: ~1 rows (approximately)
/*!40000 ALTER TABLE `attendance_ticks` DISABLE KEYS */;
/*!40000 ALTER TABLE `attendance_ticks` ENABLE KEYS */;


-- Dumping structure for table dkpbot.bids
CREATE TABLE IF NOT EXISTS `bids` (
  `item_name` varchar(100) DEFAULT NULL,
  `channel_id` varchar(50) DEFAULT NULL,
  `top_bidder` varchar(100) DEFAULT NULL,
  `top_bid_amt` int(11) DEFAULT '0',
  `second_bidder` varchar(100) DEFAULT NULL,
  `second_bid_amt` int(11) DEFAULT '0',
  `timeout_reset` int(11) DEFAULT '30',
  `timeout` varchar(100) DEFAULT '0',
  `main_has_bid` int(11) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.bids: ~0 rows (approximately)
/*!40000 ALTER TABLE `bids` DISABLE KEYS */;
/*!40000 ALTER TABLE `bids` ENABLE KEYS */;


-- Dumping structure for table dkpbot.completed_bids
CREATE TABLE IF NOT EXISTS `completed_bids` (
  `item_name` varchar(100) DEFAULT NULL,
  `winner` varchar(100) DEFAULT NULL,
  `dkp_cost` int(11) DEFAULT NULL,
  `second_place` varchar(100) DEFAULT NULL,
  `second_place_bid` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.completed_bids: ~9 rows (approximately)
/*!40000 ALTER TABLE `completed_bids` DISABLE KEYS */;
/*!40000 ALTER TABLE `completed_bids` ENABLE KEYS */;


-- Dumping structure for table dkpbot.dkp
CREATE TABLE IF NOT EXISTS `dkp` (
  `discord_id` varchar(100) DEFAULT NULL,
  `main_name` varchar(100) DEFAULT NULL,
  `dkp_value` int(11) DEFAULT '0',
  `character_class` varchar(50) DEFAULT 'NOT_SET',
  `time_registered` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `discord_id` (`discord_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.dkp: ~8 rows (approximately)
/*!40000 ALTER TABLE `dkp` DISABLE KEYS */;
/*!40000 ALTER TABLE `dkp` ENABLE KEYS */;


-- Dumping structure for table dkpbot.rolls
CREATE TABLE IF NOT EXISTS `rolls` (
  `item_name` varchar(100) DEFAULT NULL,
  `channel_id` varchar(100) DEFAULT NULL,
  `winner_id` varchar(100) DEFAULT NULL,
  `second_id` varchar(100) DEFAULT NULL,
  `winner_roll` int(11) DEFAULT '0',
  `second_roll` int(11) DEFAULT '0',
  `main_has_rolled` int(11) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Dumping data for table dkpbot.rolls: ~0 rows (approximately)
/*!40000 ALTER TABLE `rolls` DISABLE KEYS */;
/*!40000 ALTER TABLE `rolls` ENABLE KEYS */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
