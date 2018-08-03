USE koha_mapping_db;

CREATE TABLE `subscription_frequencies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `description` text COLLATE utf8_unicode_ci NOT NULL,
  `displayorder` int(11) DEFAULT NULL,
  `unit` enum('day','week','month','year') COLLATE utf8_unicode_ci DEFAULT NULL,
  `unitsperissue` int(11) NOT NULL DEFAULT '1',
  `issuesperunit` int(11) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci