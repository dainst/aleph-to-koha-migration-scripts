USE koha_mapping_db;

CREATE TABLE `aqbasketgroups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `closed` tinyint(1) DEFAULT NULL,
  `booksellerid` int(11) NOT NULL,
  `deliveryplace` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `freedeliveryplace` text COLLATE utf8_unicode_ci DEFAULT NULL,
  `deliverycomment` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `billingplace` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ALEPH_REC_KEY` varchar(25) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `booksellerid` (`booksellerid`),
  CONSTRAINT `aqbasketgroups_ibfk_1` FOREIGN KEY (`booksellerid`) REFERENCES `aqbooksellers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci