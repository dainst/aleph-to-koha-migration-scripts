USE koha_mapping_db;

CREATE TABLE `aqcontacts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `position` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `phone` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `altphone` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fax` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `notes` mediumtext COLLATE utf8_unicode_ci,
  `orderacquisition` tinyint(1) NOT NULL DEFAULT '0',
  `claimacquisition` tinyint(1) NOT NULL DEFAULT '0',
  `claimissues` tinyint(1) NOT NULL DEFAULT '0',
  `acqprimary` tinyint(1) NOT NULL DEFAULT '0',
  `serialsprimary` tinyint(1) NOT NULL DEFAULT '0',
  `booksellerid` int(11) NOT NULL,
  `ALEPH_VENDOR_CODE` varchar(25) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `booksellerid_aqcontacts_fk` (`booksellerid`),
  CONSTRAINT `booksellerid_aqcontacts_fk` FOREIGN KEY (`booksellerid`) REFERENCES `aqbooksellers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci