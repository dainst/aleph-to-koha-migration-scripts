USE koha_mapping_db;

CREATE TABLE `serialitems` (
  `itemnumber` int(11) NOT NULL,
  `serialid` int(11) NOT NULL,
  PRIMARY KEY (`itemnumber`),
  KEY `serialitems_sfk_1` (`serialid`),
  CONSTRAINT `serialitems_sfk_1` FOREIGN KEY (`serialid`) REFERENCES `serial` (`serialid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `serialitems_sfk_2` FOREIGN KEY (`itemnumber`) REFERENCES `items` (`itemnumber`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci