USE koha_mapping_db;

CREATE TABLE `serial` (
  `serialid` int(11) NOT NULL AUTO_INCREMENT,
  `biblionumber` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `subscriptionid` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `serialseq` varchar(100) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
  `serialseq_x` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `serialseq_y` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `serialseq_z` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `status` tinyint(4) NOT NULL DEFAULT 0,
  `planneddate` date DEFAULT NULL,
  `notes` text COLLATE utf8_unicode_ci DEFAULT NULL,
  `publisheddate` date DEFAULT NULL,
  `publisheddatetext` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `claimdate` date DEFAULT NULL,
  `claims_count` int(11) DEFAULT 0,
  `routingnotes` text COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`serialid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci