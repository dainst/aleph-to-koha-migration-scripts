USE koha_mapping_db;

CREATE TABLE `subscription_numberpatterns` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `label` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `displayorder` int(11) DEFAULT NULL,
  `description` text COLLATE utf8_unicode_ci NOT NULL,
  `numberingmethod` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `label1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add1` int(11) DEFAULT NULL,
  `every1` int(11) DEFAULT NULL,
  `whenmorethan1` int(11) DEFAULT NULL,
  `setto1` int(11) DEFAULT NULL,
  `numbering1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `label2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add2` int(11) DEFAULT NULL,
  `every2` int(11) DEFAULT NULL,
  `whenmorethan2` int(11) DEFAULT NULL,
  `setto2` int(11) DEFAULT NULL,
  `numbering2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `label3` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `add3` int(11) DEFAULT NULL,
  `every3` int(11) DEFAULT NULL,
  `whenmorethan3` int(11) DEFAULT NULL,
  `setto3` int(11) DEFAULT NULL,
  `numbering3` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci