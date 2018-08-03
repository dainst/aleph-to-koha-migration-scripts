USE koha_mapping_db;

CREATE TABLE `aqbudgetperiods` (
  `budget_period_id` int(11) NOT NULL AUTO_INCREMENT,
  `budget_period_startdate` date NOT NULL,
  `budget_period_enddate` date NOT NULL,
  `budget_period_active` tinyint(1) DEFAULT 0,
  `budget_period_description` mediumtext COLLATE utf8_unicode_ci DEFAULT NULL,
  `budget_period_total` decimal(28,6) DEFAULT NULL,
  `budget_period_locked` tinyint(1) DEFAULT NULL,
  `sort1_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `sort2_authcat` varchar(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ALEPH_Z76_BUDGET_NUMBER` varchar(25) NOT NULL,
  PRIMARY KEY (`budget_period_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;