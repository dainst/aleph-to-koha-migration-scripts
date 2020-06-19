USE koha_mapping_db;

CREATE TABLE `subscriptionhistory` (
  `biblionumber` int(11) NOT NULL DEFAULT '0',
  `subscriptionid` int(11) NOT NULL DEFAULT '0',
  `histstartdate` date DEFAULT NULL,
  `histenddate` date DEFAULT NULL,
  `missinglist` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `recievedlist` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `opacnote` longtext COLLATE utf8mb4_unicode_ci,
  `librariannote` longtext COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`subscriptionid`),
  KEY `biblionumber` (`biblionumber`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci