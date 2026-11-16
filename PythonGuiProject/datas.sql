-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: pos_inventory_system
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `activity_logs`
--

DROP TABLE IF EXISTS `activity_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `activity_logs` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `actor_user_id` int DEFAULT NULL,
  `actor_username` varchar(100) DEFAULT NULL,
  `actor_role` varchar(50) DEFAULT NULL,
  `action_type` varchar(100) NOT NULL,
  `target_module` varchar(100) NOT NULL DEFAULT 'General',
  `target_id` varchar(100) DEFAULT NULL,
  `description` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  KEY `idx_activity_actor_user_id` (`actor_user_id`),
  KEY `idx_activity_actor_role` (`actor_role`),
  KEY `idx_activity_action_type` (`action_type`),
  KEY `idx_activity_target_module` (`target_module`),
  KEY `idx_activity_created_at` (`created_at`),
  CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`actor_user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activity_logs`
--

LOCK TABLES `activity_logs` WRITE;
/*!40000 ALTER TABLE `activity_logs` DISABLE KEYS */;
INSERT INTO `activity_logs` VALUES (1,NULL,'System/Unknown','unknown','ADD_USER','General',NULL,'Added new cashier account: cashier','2026-05-03 08:52:15'),(2,NULL,'System/Unknown','unknown','ADD_USER','General',NULL,'Added new inventory account: inventory','2026-05-03 08:53:01'),(3,NULL,'System/Unknown','unknown','DELETE_USER','General',NULL,'Deactivated user ID 3','2026-05-03 08:53:19'),(4,NULL,'System/Unknown','unknown','RESTORE_USER','General',NULL,'Restored user ID 3','2026-05-03 08:53:36'),(5,NULL,'System/Unknown','unknown','ADD_PRODUCT','General',NULL,'Added product: paa','2026-05-03 09:00:31'),(6,NULL,'System/Unknown','unknown','EDIT_PRODUCT','General',NULL,'Edited product ID 1: paa','2026-05-03 09:01:46'),(7,NULL,'System/Unknown','unknown','ADD_PRODUCT','General',NULL,'Added product: chicken breast','2026-05-03 09:02:17'),(8,NULL,'System/Unknown','unknown','ADD_PRODUCT','General',NULL,'Added product: Whole Chicken','2026-05-03 09:04:00'),(9,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #1 with total amount 100.0','2026-05-03 09:17:48'),(10,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #1','2026-05-03 09:39:14'),(11,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #2 with total amount 560.0','2026-05-05 14:48:50'),(12,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #2','2026-05-05 14:49:22'),(13,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #3 with total amount 210.0','2026-05-05 14:50:02'),(14,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #3','2026-05-05 14:50:20'),(15,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #4 with total amount 330.0','2026-05-05 15:41:49'),(16,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #4','2026-05-05 15:42:20'),(17,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #5 with total amount 980.0','2026-05-05 15:50:55'),(18,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #6 with total amount 50.0','2026-05-05 15:51:07'),(19,NULL,'System/Unknown','unknown','CANCEL_ORDER','General',NULL,'Cancelled order #6','2026-05-05 15:51:29'),(20,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #5','2026-05-05 15:51:45'),(21,NULL,'System/Unknown','unknown','EDIT_PRODUCT','General',NULL,'Edited product ID 2: breast','2026-05-06 00:53:33'),(22,NULL,'System/Unknown','unknown','RESTORE_PRODUCT','General',NULL,'Product restored to active: Product ID 2','2026-05-06 02:10:17'),(23,NULL,'System/Unknown','unknown','DELETE_USER','General',NULL,'Deactivated user ID 2','2026-05-06 05:41:28'),(24,NULL,'System/Unknown','unknown','RESTORE_USER','General',NULL,'Restored user ID 2','2026-05-06 05:41:59'),(25,NULL,'System/Unknown','unknown','RESTORE_PRODUCT','General',NULL,'Product restored to active: Product ID 3','2026-05-06 05:45:36'),(26,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #7 with total amount 350.0','2026-05-07 09:32:50'),(27,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #7','2026-05-07 09:33:23'),(28,NULL,'System/Unknown','unknown','ADD_USER','General',NULL,'Added new cashier account: cashier2','2026-05-07 09:34:30'),(29,4,'cashier2','cashier','CREATE_ORDER','General',NULL,'Created pending order #8 with total amount 50.0','2026-05-07 09:35:16'),(30,NULL,'System/Unknown','unknown','CANCEL_ORDER','General',NULL,'Cancelled order #8','2026-05-07 09:38:25'),(31,NULL,'System/Unknown','unknown','ADD_USER','General',NULL,'Added new cashier account: asd','2026-05-07 15:54:25'),(32,NULL,'System/Unknown','unknown','DELETE_USER','General',NULL,'Deactivated user ID 3','2026-05-07 23:03:29'),(33,NULL,'System/Unknown','unknown','RESTORE_USER','General',NULL,'Restored user ID 3','2026-05-07 23:03:38'),(34,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #9 with total amount 560.0','2026-05-08 02:19:00'),(35,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #9','2026-05-08 02:19:22'),(36,NULL,'System/Unknown','unknown','DELETE_USER','General',NULL,'Deactivated user ID 4','2026-05-08 06:13:39'),(37,NULL,'System/Unknown','unknown','RESTORE_USER','General',NULL,'Restored user ID 4','2026-05-08 06:14:30'),(38,NULL,'System/Unknown','unknown','DELETE_USER','General',NULL,'Deactivated user ID 4','2026-05-08 06:24:51'),(39,NULL,'System/Unknown','unknown','RESTORE_USER','General',NULL,'Restored user ID 4','2026-05-08 06:44:19'),(40,NULL,'System/Unknown','unknown','UPDATE_USER','General',NULL,'Updated account ID 4: cashier2','2026-05-08 06:44:49'),(41,NULL,'System/Unknown','unknown','DELETE_USER','General',NULL,'Deactivated user ID 4','2026-05-08 06:44:58'),(42,NULL,'System/Unknown','unknown','ADD_PRODUCT','General',NULL,'Added product: Mendoza','2026-05-08 07:19:41'),(43,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #10 with total amount 225.0','2026-05-08 07:22:14'),(44,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #10','2026-05-08 07:25:06'),(45,NULL,'System/Unknown','unknown','DELETE_USER','General',NULL,'Deactivated user ID 2','2026-05-08 07:29:02'),(46,NULL,'System/Unknown','unknown','RESTORE_USER','General',NULL,'Restored user ID 2','2026-05-08 07:30:06'),(47,NULL,'System/Unknown','unknown','UPDATE_USER','General',NULL,'Updated account ID 2: cashier','2026-05-08 07:32:26'),(48,NULL,'System/Unknown','unknown','EDIT_PRODUCT','General',NULL,'Edited product ID 4: Mendoza','2026-05-09 10:55:55'),(49,NULL,'System/Unknown','unknown','EDIT_PRODUCT','General',NULL,'Edited product ID 4: Mendoza','2026-05-09 10:56:06'),(50,NULL,'System/Unknown','unknown','UPDATE_USER','General',NULL,'Updated account ID 2: cashier','2026-05-09 12:06:55'),(51,NULL,'System/Unknown','unknown','UPDATE_USER','General',NULL,'Updated account ID 2: cashier','2026-05-09 12:07:26'),(52,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #11 with total amount 560.0','2026-05-09 12:16:22'),(53,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #11','2026-05-09 12:16:47'),(54,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #12. Subtotal: 100.0, Discount: 20.0, Total: 80.0, Payment: Cash','2026-05-09 12:33:36'),(55,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #12','2026-05-09 12:34:24'),(56,2,'cashier','cashier','CREATE_ORDER','General',NULL,'Created pending order #13. Subtotal: 70.0, Discount: 14.0, Total: 56.0, Payment: Cash','2026-05-09 12:40:17'),(57,NULL,'System/Unknown','unknown','ACCEPT_ORDER','General',NULL,'Accepted order #13','2026-05-09 12:44:44'),(58,NULL,'System/Unknown','unknown','MARK_UNAVAILABLE','General',NULL,'Product marked unavailable: Product ID 2','2026-05-09 16:39:25'),(59,NULL,'System/Unknown','unknown','RESTORE_PRODUCT','General',NULL,'Product restored to active: Product ID 2','2026-05-09 16:39:33');
/*!40000 ALTER TABLE `activity_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_items` (
  `order_item_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `product_name` varchar(150) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `quantity` int NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  PRIMARY KEY (`order_item_id`),
  KEY `order_id` (`order_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
INSERT INTO `order_items` VALUES (1,1,1,'paa',50.00,2,100.00),(2,2,3,'Whole Chicken',280.00,2,560.00),(3,3,2,'chicken breast',70.00,3,210.00),(4,4,1,'paa',50.00,1,50.00),(5,4,3,'Whole Chicken',280.00,1,280.00),(6,5,2,'chicken breast',70.00,2,140.00),(7,5,3,'Whole Chicken',280.00,3,840.00),(8,6,1,'paa',50.00,1,50.00),(9,7,3,'Whole Chicken',280.00,1,280.00),(10,7,2,'breast',70.00,1,70.00),(11,8,1,'paa',50.00,1,50.00),(12,9,3,'Whole Chicken',280.00,2,560.00),(13,10,4,'Mendoza',15.00,15,225.00),(14,11,3,'Whole Chicken',280.00,2,560.00),(15,12,1,'paa',50.00,2,100.00),(16,13,2,'breast',70.00,1,70.00);
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `order_id` int NOT NULL AUTO_INCREMENT,
  `cashier_id` int NOT NULL,
  `subtotal_amount` decimal(10,2) DEFAULT '0.00',
  `discount_type` varchar(100) DEFAULT 'No Discount',
  `discount_amount` decimal(10,2) DEFAULT '0.00',
  `total_amount` decimal(10,2) NOT NULL DEFAULT '0.00',
  `order_status` enum('pending','accepted','cancelled') DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `accepted_at` timestamp NULL DEFAULT NULL,
  `cancelled_at` timestamp NULL DEFAULT NULL,
  `status` varchar(20) DEFAULT 'pending',
  `admin_remarks` text,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_id`),
  KEY `cashier_id` (`cashier_id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`cashier_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,2,0.00,'No Discount',0.00,100.00,'accepted','2026-05-03 09:17:48','2026-05-03 09:39:14',NULL,'accepted','Accepted by admin','2026-05-07 11:03:57'),(2,2,0.00,'No Discount',0.00,560.00,'accepted','2026-05-05 14:48:50','2026-05-05 14:49:22',NULL,'pending',NULL,'2026-05-07 09:48:53'),(3,2,0.00,'No Discount',0.00,210.00,'accepted','2026-05-05 14:50:02','2026-05-05 14:50:20',NULL,'pending',NULL,'2026-05-07 09:48:53'),(4,2,0.00,'No Discount',0.00,330.00,'accepted','2026-05-05 15:41:49','2026-05-05 15:42:20',NULL,'pending',NULL,'2026-05-07 09:48:53'),(5,2,0.00,'No Discount',0.00,980.00,'accepted','2026-05-05 15:50:55','2026-05-05 15:51:45',NULL,'pending',NULL,'2026-05-07 09:48:53'),(6,2,0.00,'No Discount',0.00,50.00,'cancelled','2026-05-05 15:51:07',NULL,'2026-05-05 15:51:29','pending',NULL,'2026-05-07 09:48:53'),(7,2,0.00,'No Discount',0.00,350.00,'accepted','2026-05-07 09:32:50','2026-05-07 09:33:23',NULL,'pending',NULL,'2026-05-07 09:48:53'),(8,4,0.00,'No Discount',0.00,50.00,'cancelled','2026-05-07 09:35:16',NULL,'2026-05-07 09:38:25','pending',NULL,'2026-05-07 09:48:53'),(9,2,0.00,'No Discount',0.00,560.00,'accepted','2026-05-08 02:19:00','2026-05-08 02:19:22',NULL,'pending',NULL,'2026-05-08 02:19:22'),(10,2,0.00,'No Discount',0.00,225.00,'accepted','2026-05-08 07:22:14','2026-05-08 07:25:06',NULL,'pending',NULL,'2026-05-08 07:25:06'),(11,2,0.00,'No Discount',0.00,560.00,'accepted','2026-05-09 12:16:22','2026-05-09 12:16:47',NULL,'pending',NULL,'2026-05-09 12:16:47'),(12,2,100.00,'PWD Discount - 20%',20.00,80.00,'accepted','2026-05-09 12:33:36','2026-05-09 12:34:24',NULL,'pending',NULL,'2026-05-09 12:34:24'),(13,2,70.00,'PWD Discount - 20%',14.00,56.00,'accepted','2026-05-09 12:40:17','2026-05-09 12:44:44',NULL,'pending',NULL,'2026-05-09 12:44:44');
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `amount_received` decimal(10,2) NOT NULL,
  `change_amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(50) DEFAULT 'Cash',
  `online_reference` varchar(150) DEFAULT NULL,
  `paid_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`payment_id`),
  UNIQUE KEY `order_id` (`order_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
INSERT INTO `payments` VALUES (1,1,110.00,10.00,'Cash',NULL,'2026-05-03 09:17:48'),(2,2,561.00,1.00,'Cash',NULL,'2026-05-05 14:48:50'),(3,3,300.00,90.00,'Cash',NULL,'2026-05-05 14:50:02'),(4,4,350.00,20.00,'Cash',NULL,'2026-05-05 15:41:49'),(5,5,1000.00,20.00,'Cash',NULL,'2026-05-05 15:50:55'),(6,6,70.00,20.00,'Cash',NULL,'2026-05-05 15:51:07'),(7,7,1000.00,650.00,'Cash',NULL,'2026-05-07 09:32:50'),(8,8,50.00,0.00,'Cash',NULL,'2026-05-07 09:35:16'),(9,9,600.00,40.00,'Cash',NULL,'2026-05-08 02:19:00'),(10,10,500.10,275.10,'Cash',NULL,'2026-05-08 07:22:14'),(11,11,560.00,0.00,'Cash',NULL,'2026-05-09 12:16:22'),(12,12,100.00,20.00,'Cash','','2026-05-09 12:33:36'),(13,13,70.00,14.00,'Cash','','2026-05-09 12:40:17');
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `product_id` int NOT NULL AUTO_INCREMENT,
  `product_name` varchar(150) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `unit` varchar(50) NOT NULL,
  `quantity` int NOT NULL DEFAULT '0',
  `status` enum('active','inactive') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`product_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'paa',50.00,'30',15,'active','2026-05-03 09:00:31','2026-05-09 12:34:24'),(2,'breast',70.00,'50',43,'active','2026-05-03 09:02:17','2026-05-09 16:39:33'),(3,'Whole Chicken',280.00,'50',9,'active','2026-05-03 09:04:00','2026-05-09 12:16:47'),(4,'Mendoza',15.00,'20kg',2,'active','2026-05-08 07:19:41','2026-05-09 10:56:05');
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_movements`
--

DROP TABLE IF EXISTS `stock_movements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_movements` (
  `movement_id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `movement_type` enum('add','edit','delete','sale','restock') NOT NULL,
  `quantity_changed` int NOT NULL,
  `remarks` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`movement_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `stock_movements_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_movements`
--

LOCK TABLES `stock_movements` WRITE;
/*!40000 ALTER TABLE `stock_movements` DISABLE KEYS */;
INSERT INTO `stock_movements` VALUES (1,1,'add',20,'Initial product stock','2026-05-03 09:00:31'),(2,2,'add',50,'Initial product stock','2026-05-03 09:02:18'),(3,3,'add',20,'Initial product stock','2026-05-03 09:04:00'),(4,1,'sale',-2,'Sold from accepted order #1','2026-05-03 09:39:14'),(5,3,'sale',-2,'Sold from accepted order #2','2026-05-05 14:49:22'),(6,2,'sale',-3,'Sold from accepted order #3','2026-05-05 14:50:20'),(7,1,'sale',-1,'Sold from accepted order #4','2026-05-05 15:42:20'),(8,3,'sale',-1,'Sold from accepted order #4','2026-05-05 15:42:20'),(9,2,'sale',-2,'Sold from accepted order #5','2026-05-05 15:51:45'),(10,3,'sale',-3,'Sold from accepted order #5','2026-05-05 15:51:45'),(11,3,'sale',-1,'Sold from accepted order #7','2026-05-07 09:33:23'),(12,2,'sale',-1,'Sold from accepted order #7','2026-05-07 09:33:23'),(13,3,'sale',-2,'Sold from accepted order #9','2026-05-08 02:19:22'),(14,4,'add',15,'Initial product stock','2026-05-08 07:19:41'),(15,4,'sale',-15,'Sold from accepted order #10','2026-05-08 07:25:06'),(16,4,'edit',2,'Product stock updated','2026-05-09 10:56:06'),(17,3,'sale',-2,'Sold from accepted order #11','2026-05-09 12:16:47'),(18,1,'sale',-2,'Sold from accepted order #12','2026-05-09 12:34:24'),(19,2,'sale',-1,'Sold from accepted order #13','2026-05-09 12:44:44'),(20,2,'delete',0,'Product marked unavailable','2026-05-09 16:39:25');
/*!40000 ALTER TABLE `stock_movements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','cashier','inventory') NOT NULL,
  `status` enum('active','inactive') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'System Administrator','admin','admin123','admin','active','2026-04-30 08:54:37'),(2,'CASHIER01','cashier','qweQWE1!','cashier','active','2026-05-03 08:52:15'),(3,'INVENTORY01','inventory','inventory123','inventory','active','2026-05-03 08:53:01'),(4,'cashier21','cashier2','asdASD1!','cashier','inactive','2026-05-07 09:34:30');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-10 11:45:14
