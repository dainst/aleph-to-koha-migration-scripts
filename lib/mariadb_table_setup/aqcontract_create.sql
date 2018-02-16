USE koha_mapping_db;

CREATE TABLE `aqcontract` (
  `contractnumber` int(11) NOT NULL AUTO_INCREMENT,
  `contractstartdate` date DEFAULT NULL,
  `contractenddate` date DEFAULT NULL,
  `contractname` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `contractdescription` mediumtext COLLATE utf8_unicode_ci DEFAULT NULL,
  `booksellerid` int(11) NOT NULL,
  PRIMARY KEY (`contractnumber`),
  KEY `booksellerid_fk1` (`booksellerid`),
  CONSTRAINT `booksellerid_fk1` FOREIGN KEY (`booksellerid`) REFERENCES `aqbooksellers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci